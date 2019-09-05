# Users and Groups
Design of the user and group management and related things.

Ingest methods: CSV, JSON, CLI prompts

# Types
Type: user
* name: the short name to refer to the user, e.g. "goesc".
* fullName: full name of the user (Optional)
* password: plaintext password to use (Optional, if left blank will be automatically generated)
* domain: windows domain user belongs to (Optional)
* groups: groups the user belongs to, as a list (Optional)

Type: standard-group
* name: name of the group
* description: description of the group (Optional)
* permissions: (TODO)

Type: instanced-group
* basename: base name of the group
* instances: number of instances of this group to create
* description: description of the group (Optional)

These are what were previously called "Template groups"
They generate a large number of groups with the same base name.
This enables creation of, say, 15 teams of 3 users for an exercise.
Users assigned to this group will be placed in *one* of the instances.

Type: ad  (TODO: shelve these for now...)
* name: Name of the AD group
* domain: The domain the AD group belongs to (Optional)

# Misc.
* Spaces and other whitespace will be removed from all names and passwords

* All users are, by default, in the "default" group.
* Users can be part of multiple groups
* VMs and other things can have groups and/or specific users assigned to them
* All users in assigned groups or directly assigned will be provided access
* to the VM or other thing. This could be SSH, RDP, the platform's management
* GUI, whatever.

# Directory structure
* There will be a directory created for user artifacts: Users
* There will be a sub-directory for each user, containing information for that user.

```
adles_output/
  adles_state.db  # This would be API keys, hostnames, etc.
  user_data/
      user_metadata.json
      user1/
          user1_rsa_key.public
          user1_rsa_key.private
          some_flag_1.txt
          HKEY_LOCAL_USERS.reg
          ...
      user2/
          ...
      ...
```
