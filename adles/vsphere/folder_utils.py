import logging

from pyVmomi import vim

from adles.utils import split_path
from adles.vsphere.vsphere_utils import is_folder, is_vm


def create_folder(folder, folder_name):
    """
    Creates a VM folder in the specified folder.

    :param folder: Folder to create the folder in
    :type folder: vim.Folder
    :param str folder_name: Name of folder to create
    :return: The created folder
    :rtype: vim.Folder or None
    """
    # Check if the folder already exists
    exists = find_in_folder(folder, folder_name)
    if exists:
        logging.warning("Folder '%s' already exists in folder '%s'",
                        folder_name, folder.name)
        return exists  # Return the folder that already existed
    else:
        logging.debug("Creating folder '%s' in folder '%s'",
                      folder_name, folder.name)
        try:
            # Create the folder and return it
            return folder.CreateFolder(folder_name)
        except vim.fault.DuplicateName as dupe:
            logging.error("Could not create folder '%s' in '%s': "
                          "folder already exists as '%s'",
                          folder_name, folder.name, dupe.name)
        except vim.fault.InvalidName as invalid:
            logging.error("Could not create folder '%s' in '%s': "
                          "Invalid folder name '%s'",
                          folder_name, folder.name, invalid.name)
    return None


def cleanup(folder, vm_prefix='', folder_prefix='', recursive=False,
            destroy_folders=False, destroy_self=False):
    """
    Cleans a folder by selectively destroying any VMs and folders it contains.

    :param folder: Folder to cleanup
    :type folder: vim.Folder
    :param str vm_prefix: Only destroy VMs with names starting with the prefix
    :param str folder_prefix: Only destroy or search in folders with names
    starting with the prefix
    :param bool recursive: Recursively descend into any sub-folders
    :param bool destroy_folders: Destroy folders in addition to VMs
    :param bool destroy_self: Destroy the folder specified
    """
    logging.debug("Cleaning folder '%s'", folder.name)
    from adles.vsphere.vm import VM

    # TODO: progress bar
    # pbar = tqdm.tqdm(folder.childEntity, desc="Cleaning folder",
    #                  unit="Items", clear=True)
    for item in folder.childEntity:
        # Handle VMs
        if is_vm(item) and str(item.name).startswith(vm_prefix):
            VM(vm=item).destroy()  # Delete the VM from the Datastore

        # Handle folders
        elif is_folder(item) and str(item.name).startswith(folder_prefix):
            if destroy_folders:  # Destroys folder and ALL of it's sub-objects
                cleanup(item, destroy_folders=True, destroy_self=True)
            elif recursive:  # Simply recurses to find more items
                cleanup(item, vm_prefix=vm_prefix,
                        folder_prefix=folder_prefix, recursive=True)

    # Note: UnregisterAndDestroy does NOT delete VM files off the datastore
    # Only use if folder is already empty!
    if destroy_self:
        logging.debug("Destroying folder: '%s'", folder.name)
        folder.UnregisterAndDestroy_Task().wait()


def get_in_folder(folder, name, recursive=False, vimtype=None):
    """
    Retrieves an item from a datacenter folder.

    :param folder: Folder to search in
    :type folder: vim.Folder
    :param str name: Name of object to find
    :param bool recursive: Recurse into sub-folders
    :param vimtype: Type of object to search for
    :return: The object found
    :rtype: vimtype or None
    """
    item = None
    if name is not None:
        item = find_in_folder(folder, name, recursive=recursive,
                              vimtype=vimtype)

    # Get first found of type if can't find in folder or name isn't specified
    if item is None:
        if len(folder.childEntity) > 0 and vimtype is None:
            return folder.childEntity[0]
        elif len(folder.childEntity) > 0:
            for i in folder.childEntity:
                if isinstance(i, vimtype):
                    return i
            logging.error("Could not find item of type '%s' in folder '%s'",
                          vimtype.__name__, folder.name)
        else:
            logging.error("There are no items in folder %s", folder.name)
    return item


def find_in_folder(folder, name, recursive=False, vimtype=None):
    """
    Finds and returns an specific object in a folder.

    :param folder: Folder to search in
    :type folder: vim.Folder
    :param str name: Name of the object to find
    :param bool recursive: Recurse into sub-folders
    :param vimtype: Type of object to search for
    :return: The object found
    :rtype: vimtype or None
    """
    # NOTE: Convert to lowercase for case-insensitive comparisons
    item_name = name.lower()
    found = None
    for item in folder.childEntity:
        # Check if the name matches
        if hasattr(item, 'name') and item.name.lower() == item_name:
            if vimtype is not None and not isinstance(item, vimtype):
                continue
            found = item
        elif recursive and is_folder(item):  # Recurse into sub-folders
            found = find_in_folder(item, name=item_name,
                                   recursive=recursive, vimtype=vimtype)
        if found is not None:
            return found
    return None


def traverse_path(folder, path, lookup_root=None, generate=False):
    """
    Traverses a folder path to find a object with a specific name.

    :param folder: Folder to search in
    :type folder: vim.Folder
    :param str path: Path in POSIX format
    (Templates/Windows/ to get the 'Windows' folder)
    :param lookup_root: If root of path is not found in folder,
    lookup using this Vsphere object
    :type lookup_root: :class:`Vsphere` or None
    :param bool generate: Parts of the path that do not exist are created.
    :return: Object at the end of the path
    :rtype: vimtype or None
    """
    logging.debug("Traversing path '%s' from folder '%s'", path, folder.name)
    folder_path, name = split_path(path)

    # Check if root of the path is in the folder
    # This is to allow relative paths to be used if lookup_root is defined
    folder_items = [x.name.lower() for x in folder.childEntity
                    if hasattr(x, 'name')]
    if len(folder_path) > 0 and folder_path[0] not in folder_items:
        if lookup_root is not None:
            logging.debug("Root %s not in folder %s, looking up...",
                          folder_path[0], folder.name)
            # Lookup the path root on server
            folder = lookup_root.get_folder(folder_path.pop(0))
        else:
            logging.error("Could not find root '%s' "
                          "of path '%s' in folder '%s'",
                          folder_path[0], path, folder.name)
            return None

    current = folder  # Start with the defined folder
    for f in folder_path:  # Try each folder name in the path
        found = None

        # Iterate through items in the current folder
        for item in current.childEntity:
            # If Folder is part of path
            if is_folder(item) and item.name.lower() == f:
                found = item  # This is the next folder in the path
                # Break to outer loop to check this folder
                # for the next part of the path
                break
        if generate and found is None:  # Can't find the folder, so create it
            logging.warning("Generating folder %s in path", f)
            create_folder(folder, f)  # Generate the folder
        elif found is not None:
            current = found

    # Since the split had a basename, look for an item with matching name
    if name != '':
        return find_in_folder(current, name)
    else:  # No basename, so just return whatever was at the end of the path
        return current


def enumerate_folder(folder, recursive=True, power_status=False):
    """
    Enumerates a folder structure and returns the result.

    as a python object with the same structure
    :param folder: Folder to enumerate
    :type folder: vim.Folder
    :param bool recursive: Whether to recurse into any sub-folders
    :param bool power_status: Display the power state of the VMs in the folder
    :return: The nested python object with the enumerated folder structure
    :rtype: list(list, str)
    """
    children = []
    for item in folder.childEntity:
        if is_folder(item):
            if recursive:  # Recurse into sub-folders and append the sub-tree
                children.append(enumerate_folder(item, recursive))
            else:  # Don't recurse, just append the folder
                children.append('- ' + item.name)
        elif is_vm(item):
            if power_status:
                if item.runtime.powerState == \
                        vim.VirtualMachine.PowerState.poweredOn:
                    children.append('* ON  ' + item.name)
                elif item.runtime.powerState == \
                        vim.VirtualMachine.PowerState.poweredOff:
                    children.append('* OFF ' + item.name)
                elif item.runtime.powerState == \
                        vim.VirtualMachine.PowerState.suspended:
                    children.append('* SUS ' + item.name)
                else:
                    logging.error("Invalid power state for VM: %s", item.name)
            else:
                children.append('* ' + item.name)
        else:
            children.append("UNKNOWN ITEM: %s" % str(item))
    return '+ ' + folder.name, children  # Return tuple of parent and children


# Similar to: https://docs.python.org/3/library/pprint.html
def format_structure(structure, indent=4, _depth=0):
    """
    Converts a nested structure of folders into a formatted string.

    :param structure: structure to format
    :type structure: tuple(list(str), str)
    :param int indent: Number of spaces to indent each level of nesting
    :param int _depth: Current depth (USED INTERNALLY BY FUNCTION)
    :return: Formatted string of the folder structure
    :rtype: str
    """
    fmat = ""
    newline = '\n' + str(_depth * str(indent * ' '))

    if isinstance(structure, tuple):
        fmat += newline + str(structure[0])
        fmat += format_structure(structure[1], indent, _depth + 1)
    elif isinstance(structure, list):
        for item in structure:
            fmat += format_structure(item, indent, _depth)
    elif isinstance(structure, str):
        fmat += newline + structure
    else:
        logging.error("Unexpected type in folder structure for item '%s': %s",
                      str(structure), type(structure))
    return fmat


def retrieve_items(folder, vm_prefix='', folder_prefix='', recursive=False):
    """
    Retrieves VMs and folders from a folder structure.

    :param folder: Folder to begin search in
    (Note: it is NOT returned in list of folders)
    :type folder: vim.Folder
    :param str vm_prefix: VM prefix to search for
    :param str folder_prefix: Folder prefix to search for
    :param bool recursive: Recursively descend into sub-folders

    .. warning:: This will recurse regardless of folder prefix!

    :return: The VMs and folders found in the folder
    :rtype: tuple(list(vim.VirtualMachine), list(vim.Folder))
    """
    vms = []
    folders = []

    for item in folder.childEntity:  # Iterate through all items in the folder
        if is_vm(item) and str(item.name).startswith(vm_prefix):
            vms.append(item)  # Add matching vm to the list
        elif is_folder(item):
            if str(item.name).startswith(folder_prefix):
                folders.append(item)  # Add matching folder to the list
            if recursive:  # Recurse into sub-folders
                v, f = retrieve_items(item, vm_prefix, folder_prefix, recursive)
                vms.extend(v)
                folders.extend(f)
    return vms, folders


def move_into(folder, entity_list):
    """
    Moves a list of managed entities into the named folder.

    :param folder: Folder to move entities into
    :type folder: vim.Folder
    :param entity_list: Entities to move into the folder
    :type entity_list: list(vim.ManagedEntity)
    """
    logging.debug("Moving a list of %d entities into folder %s",
                  len(entity_list), folder.name)
    folder.MoveIntoFolder_Task(entity_list).wait()


def rename(folder, name):
    """
    Renames a folder.

    :param folder: Folder to rename
    :type folder: vim.Folder
    :param str name: New name for the folder
    """
    logging.debug("Renaming %s to %s", folder.name, name)
    folder.Rename_Task(newName=str(name)).wait()


# Injection of methods into vim.Folder pyVmomi class
#
# These enable "<folder>.create('name')" instead of
# "folder_utils.create_folder(<folder>, 'name')"
#
# This works because the implicit first argument
# to a class method call in Python is the instance
#
vim.Folder.create = create_folder
vim.Folder.cleanup = cleanup
vim.Folder.get = get_in_folder
vim.Folder.find_in = find_in_folder
vim.Folder.traverse_path = traverse_path
vim.Folder.enumerate = enumerate_folder
vim.Folder.retrieve_items = retrieve_items
vim.Folder.move_into = move_into
vim.Folder.rename = rename
