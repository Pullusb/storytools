# SPDX-License-Identifier: GPL-3.0-or-later

"""Generic backup / restore helpers for addon preferences and keymaps (RNA <-> json)

Self contained: only depends on `bpy` and the standard library.
Everything addon specific is passed in
by the caller (preferences, operator idnames, side effects to replay)

--- For host addon ---

1. Values are written with `setattr`, never with raw ID-property assignment.
   (`obj["prop"] = value` is unsupported since Blender 5.0.)
   As a consequence `update=` callbacks fire on write, see point 2.

2. Every `update=` callback on the preferences, and on any PropertyGroup they contain,
   must return early while `is_restoring()` is true:

       def my_update(self, context):
           from .prefs_io_core import is_restoring
           if is_restoring():
               return
           ...

   If ommitted, it will fire mid-restore, on half written preferences. Callbacks that
   register/unregister classes raise outright, others can silently corrupt values.

3. The host replays the suppressed side effects once, after the `restoring()` block
   has exited.

4. PointerProperty to an ID datablock (Object, Material...) is skipped by design:
   there is no reliable way to re-link it.
"""

import bpy

from contextlib import contextmanager

## Properties that never carry transferable data
DEFAULT_SKIP = frozenset(('rna_type', 'bl_idname'))

## Keymap item event attributes to store
## (plain getattr/setattr, so their type can change across Blender versions)
KMI_ATTRS = ('map_type', 'type', 'value', 'any', 'ctrl', 'shift', 'alt', 'oskey',
             'key_modifier', 'repeat', 'active')


# region restore guard

_restoring = False

def is_restoring():
    """True while preferences are being restored from a backup
    Property `update=` callbacks must return early using this is_restoring() condition"""
    return _restoring


@contextmanager
def restoring():
    """Suppress the cooperating `update=` callbacks for the duration of the block"""
    global _restoring
    previous = _restoring
    _restoring = True
    try:
        yield
    finally:
        _restoring = previous


# region class registration

def is_class_registered(cls):
    """True when `cls` is currently registered

    Registration sets `bl_rna` on the class itself and unregistration removes it.
    Checked on __dict__ because `bl_rna` is also inherited from the base type, and
    because GizmoGroup classes never show up in `bpy.types` nor expose
    `is_registered` (unlike Panel), so neither of those can be used here"""
    return 'bl_rna' in cls.__dict__


def set_class_registered(cls, enabled):
    """Register or unregister `cls` so that its state matches `enabled`
    Return True when the registration state actually changed"""
    registered = is_class_registered(cls)
    if enabled and not registered:
        bpy.utils.register_class(cls)
        return True
    if not enabled and registered:
        bpy.utils.unregister_class(cls)
        return True
    return False


# region generic RNA <-> json

def prop_to_json(owner, skip=None, only_set=False):
    """Recursively dump an RNA struct (AddonPreferences, PropertyGroup,
    OperatorProperties...) to a json compatible dict

    only_set: skips the properties that were never explicitly assigned.
        Used for keymap item properties: `template_keymap_item_properties()` 
        greys out the unset ones
    """
    skip = DEFAULT_SKIP if skip is None else skip
    data = {}
    for name, prop in owner.bl_rna.properties.items():
        if name in skip:
            continue
        ## Note: PointerProperty and CollectionProperty are flagged read-only
        ## (the pointer itself cannot be reassigned) but their content is writable
        if prop.is_readonly and prop.type not in ('POINTER', 'COLLECTION'):
            continue
        if only_set and not owner.is_property_set(name):
            continue

        value = getattr(owner, name)

        if prop.type == 'POINTER':
            ## Only descend into owned PropertyGroups, never into ID datablocks
            if not isinstance(value, bpy.types.PropertyGroup):
                continue
            data[name] = prop_to_json(value, skip=skip)
        elif prop.type == 'COLLECTION':
            data[name] = [prop_to_json(item, skip=skip) for item in value]
        elif prop.type == 'ENUM':
            ## Store identifier(s), not the underlying int (ints can be reshuffled)
            data[name] = sorted(value) if prop.is_enum_flag else value
        elif getattr(prop, 'is_array', False):
            data[name] = list(value)
        else:
            data[name] = value

    return data


def _validate_enum(prop, value, path, log):
    """Check that the stored identifier(s) still exist on this enum
    Return the value to assign (a set for flag enums), or None to skip the property"""
    if prop.is_enum_flag:
        if not isinstance(value, (list, tuple)):
            log.append(f'{path}: expected a list of enum identifiers, got {type(value).__name__}')
            return None
        known = {i for i in value if prop.enum_items.get(i) is not None}
        for identifier in value:
            if identifier not in known:
                log.append(f'{path}: unknown enum identifier "{identifier}"')
        ## Nothing left: leave the property alone rather than clearing it
        return known or None

    if not isinstance(value, str):
        log.append(f'{path}: expected an enum identifier, got {type(value).__name__}')
        return None
    if prop.enum_items.get(value) is None:
        log.append(f'{path}: unknown enum identifier "{value}"')
        return None
    return value


def _clamp(prop, value):
    """Keep hand edited files within the property range
    (RNA clamps too, this only makes the intent explicit)"""
    if isinstance(value, (list, tuple)):
        return [_clamp(prop, v) for v in value]
    if isinstance(value, bool):
        return value
    return min(max(value, prop.hard_min), prop.hard_max)


def _assign(owner, name, value, sub_path, log):
    """Write a value through RNA

    Deliberately not using raw ID-property assignment (owner[name] = value):
    Reaching the IDProperty storage backing a bpy.props property
    is discouraged/unsupported. 
    `update=` callbacks are suppressed by the `restoring()` guard instead"""
    try:
        setattr(owner, name, value)
    except (TypeError, ValueError) as e:
        log.append(f'{sub_path}: {e}')


def json_to_prop(owner, data, path='', log=None, skip=None):
    """Recursively apply a json dict on an RNA struct
    Unknown / renamed / removed entries are skipped and appended to `log`
    Must be called inside `restoring()` when `owner` is the addon preferences"""
    if log is None:
        log = []
    skip = DEFAULT_SKIP if skip is None else skip

    if not isinstance(data, dict):
        log.append(f'{path or "<root>"}: expected a dict, got {type(data).__name__}')
        return log

    props = owner.bl_rna.properties
    for name, value in data.items():
        if name in skip:
            continue

        sub_path = f'{path}.{name}' if path else name

        prop = props.get(name)
        if prop is None:
            log.append(f'{sub_path}: no such property (removed or renamed)')
            continue
        ## Pointer/Collection are read-only as pointers, but their content is writable
        if prop.is_readonly and prop.type not in ('POINTER', 'COLLECTION'):
            log.append(f'{sub_path}: property is read-only')
            continue

        if prop.type == 'POINTER':
            target = getattr(owner, name)
            if not isinstance(target, bpy.types.PropertyGroup):
                log.append(f'{sub_path}: not a property group, skipped')
                continue
            json_to_prop(target, value, path=sub_path, log=log, skip=skip)

        elif prop.type == 'COLLECTION':
            if not isinstance(value, list):
                log.append(f'{sub_path}: expected a list, got {type(value).__name__}')
                continue
            collection = getattr(owner, name)
            collection.clear()
            for i, item_data in enumerate(value):
                json_to_prop(collection.add(), item_data,
                             path=f'{sub_path}[{i}]', log=log, skip=skip)

        elif prop.type == 'ENUM':
            ## Validated first so a stale identifier gets a clear log line
            enum_value = _validate_enum(prop, value, sub_path, log)
            if enum_value is not None:
                _assign(owner, name, enum_value, sub_path, log)

        elif getattr(prop, 'is_array', False):
            if not isinstance(value, (list, tuple)):
                log.append(f'{sub_path}: expected a list, got {type(value).__name__}')
                continue
            if len(value) != prop.array_length:
                log.append(f'{sub_path}: expected {prop.array_length} values, got {len(value)}')
                continue
            _assign(owner, name, _clamp(prop, list(value)), sub_path, log)

        elif prop.type == 'STRING':
            if not isinstance(value, str):
                log.append(f'{sub_path}: expected a string, got {type(value).__name__}')
                continue
            _assign(owner, name, value, sub_path, log)

        elif prop.type == 'BOOLEAN':
            _assign(owner, name, bool(value), sub_path, log)

        elif prop.type in ('INT', 'FLOAT'):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                log.append(f'{sub_path}: expected a number, got {type(value).__name__}')
                continue
            _assign(owner, name, _clamp(prop, int(value) if prop.type == 'INT' else float(value)),
                    sub_path, log)

        else:
            log.append(f'{sub_path}: unsupported property type "{prop.type}"')

    return log


# region keymap items

def _as_idname_set(idnames):
    """Accept a single operator idname or an iterable of them"""
    if isinstance(idnames, str):
        return {idnames}
    return set(idnames)


def _keymap_items(km, idnames, user_defined=None):
    items = [kmi for kmi in km.keymap_items if kmi.idname in idnames]
    if user_defined is None:
        return items
    return [kmi for kmi in items if kmi.is_user_defined == user_defined]


def _kmi_to_json(kmi):
    data = {'idname': kmi.idname}
    for attr in KMI_ATTRS:
        if hasattr(kmi, attr):
            data[attr] = getattr(kmi, attr)
    ## Only the explicitly assigned properties, so the untouched ones stay unset
    ## (and keep showing as greyed / unmodified) after a restore.
    ## DEFAULT_SKIP, not the host skip set: operator properties are their own namespace
    data['properties'] = prop_to_json(kmi.properties, only_set=True)
    return data


def _json_to_kmi(kmi, data, path, log):
    ## map_type first: drives which event fields are valid
    for attr in KMI_ATTRS:
        if attr not in data or not hasattr(kmi, attr):
            continue
        try:
            setattr(kmi, attr, data[attr])
        except (TypeError, ValueError) as e:
            log.append(f'{path}.{attr}: {e}')

    ## Clear the properties the backup recorded as untouched, so they keep showing unset.
    ## Only those: unsetting a property that the addon assigned on its
    ## own default keymap item would wipe that value instead of restoring it.
    properties = kmi.properties
    stored = data.get('properties', {})
    for name in properties.bl_rna.properties.keys():
        if name in DEFAULT_SKIP or name in stored:
            continue
        try:
            properties.property_unset(name)
        except (TypeError, RuntimeError) as e:
            log.append(f'{path}.properties.{name}: could not unset ({e})')

    json_to_prop(properties, stored, path=f'{path}.properties', log=log)


def _resolve_keymap(kc, km_name, km_aliases):
    """Find a keymap by name, falling back to the given interchangeable names
    (keymaps get renamed across Blender versions)"""
    km = kc.keymaps.get(km_name)
    if km is not None:
        return km
    if km_name in km_aliases:
        for alias in km_aliases:
            km = kc.keymaps.get(alias)
            if km is not None:
                return km
    return None


def keymap_items_to_json(idnames, km_aliases=()):
    """Dump the user keyconfig keymap items whose operator is in `idnames`

    Addon provided items are stored by order of appearance (a restore reverts them
    to default then re-applies the stored state), user created ones are stored so
    they can be recreated from scratch"""
    idnames = _as_idname_set(idnames)
    kc = bpy.context.window_manager.keyconfigs.user
    data = {}
    for km in kc.keymaps:
        items = _keymap_items(km, idnames)
        if not items:
            continue
        data[km.name] = {
            'addon': [_kmi_to_json(kmi) for kmi in items if not kmi.is_user_defined],
            'user': [_kmi_to_json(kmi) for kmi in items if kmi.is_user_defined],
        }
    return data


def reset_keymap_items(idnames, label='Addon'):
    """Bring the matching keymap items back to the addon defaults:
    delete the user created ones, revert the addon provided ones"""
    idnames = _as_idname_set(idnames)
    kc = bpy.context.window_manager.keyconfigs.user
    for km in kc.keymaps:
        ## Removing invalidates the other python references, re-scan each time
        for _ in range(200): # safety bound
            kmi = next(iter(_keymap_items(km, idnames, user_defined=True)), None)
            if kmi is None:
                break
            km.keymap_items.remove(kmi)

        ## Revert unconditionally: `is_user_modified` is only set through the
        ## preferences UI, an item edited another way would stay untouched
        for i in range(len(_keymap_items(km, idnames, user_defined=False))):
            items = _keymap_items(km, idnames, user_defined=False)
            if i >= len(items):
                break
            try:
                km.restore_item_to_default(items[i])
            except (RuntimeError, TypeError) as e:
                print(f'[{label}] Could not reset keymap item in "{km.name}": {e}')


def json_to_keymap_items(data, idnames, km_aliases=(), log=None, label='Addon'):
    """Replace all matching keymap items with the ones stored in `data`"""
    if log is None:
        log = []
    if not isinstance(data, dict):
        log.append('keymaps: expected a dict, skipped')
        return log

    idnames = _as_idname_set(idnames)
    ## Used when recreating user items saved before `idname` was stored per item
    default_idname = next(iter(sorted(idnames)))

    reset_keymap_items(idnames, label=label)

    kc = bpy.context.window_manager.keyconfigs.user
    for km_name, entry in data.items():
        km = _resolve_keymap(kc, km_name, km_aliases)
        if km is None:
            if not entry.get('user'):
                ## Nothing to recreate, addon items of an unknown keymap are gone
                log.append(f'keymaps: keymap "{km_name}" not found')
                continue
            km = kc.keymaps.new(name=km_name, space_type='EMPTY')

        ## Addon provided items: freshly restored to default, re-apply stored state by order
        addon_kmis = _keymap_items(km, idnames, user_defined=False)
        addon_data = entry.get('addon', [])
        if len(addon_data) > len(addon_kmis):
            log.append(f'keymaps: "{km_name}" had {len(addon_data)} default items '
                       f'in backup, addon now provides {len(addon_kmis)}')
        for i, kmi_data in enumerate(addon_data[:len(addon_kmis)]):
            _json_to_kmi(addon_kmis[i], kmi_data, f'keymaps.{km_name}.addon[{i}]', log)

        ## User created items: recreate from scratch
        for i, kmi_data in enumerate(entry.get('user', [])):
            idname = kmi_data.get('idname', default_idname)
            if idname not in idnames:
                log.append(f'keymaps.{km_name}.user[{i}]: unexpected idname "{idname}", skipped')
                continue
            kmi = km.keymap_items.new(idname, type='NONE', value='PRESS')
            _json_to_kmi(kmi, kmi_data, f'keymaps.{km_name}.user[{i}]', log)

    return log


# region misc

def get_addon_version(package_name):
    """Return the addon version as a string, empty when it cannot be resolved"""
    try:
        import sys
        import addon_utils
        module = sys.modules.get(package_name)
        if module is None:
            return ''
        info = addon_utils.module_bl_info(module)
        return '.'.join(str(v) for v in info.get('version', ()))
    except Exception as e:
        print(f'Could not resolve addon version for "{package_name}": {e}')
        return ''


def log_report(log, prefix, label='Addon'):
    """Print the skipped entries in console only, return how many there were"""
    if not log:
        return 0
    print(f'\n[{label}] {prefix}: {len(log)} entrie(s) skipped')
    for line in log:
        print(f'  - {line}')
    print()
    return len(log)
