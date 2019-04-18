# -*- coding: utf-8 -*-
'''
create and install configuration profiles.

 .. code-block:: yaml

    example_state_profile:
      profile.installed:
        - name: example name
        - description: 'Example Description'
        - displayname: 'Managing a Preference'
        - organization: MegaCorp
        - removaldisallowed: True
        - scope: System
        - content:
            - PayloadType: com.apple.ManagedClient.preferences
              PayloadContent:
                com.megacorp.preference: <- preference domain
                  Forced:
                    - mcx_preference_settings:
                        ExamplePreferenceKey: True
                ...

'''


import logging
import pprint

import salt.exceptions
import salt.utils
import salt.utils.platform


log = logging.getLogger(__name__)

__virtualname__ = 'profile'


def __virtual__():
    if salt.utils.platform.is_darwin():
        return __virtualname__

    return (False, 'state.profile only available on macOS.')


def installed(name, force=None, **kwargs):
    '''
    Create and install the specified configuration profile, using the supplied payload content.
    This state module is not intended to be used at the command line.

    name:
        The name of the resource is the payload identifier, which is used to determine whether the payload is
        installed.

    force:
        True or False, will overwrite existing profile with the same name.

    Keyword Arguments:

        description:
            Description shown below profile name in profile preferences.

        displayname:
            The main title shown that identifies the profile.

        organization:
            The organization responsible for creating the profile.

        removaldisallowed:
            Whether or not to disallow removal of this profile.

        content:
            The payload data contained within this profile. Should be generated by another formula.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    exists = __salt__['profile.exists'](name)

    content = __salt__['profile.generate'](
        name,
        None,
        **kwargs
    )

    valid = __salt__['profile.validate'](name, content)

    if exists and valid['installed']:
        ret['comment'] = 'Profile identifier "{}", already installed.'.format(name)
        return ret

    mcpath = __salt__['temp.file']('.mobileconfig', 'salt')
    f = open(mcpath, "wb")
    f.write(content)
    f.close()

    log.debug('Wrote .mobileconfig in secure temporary location: {}'.format(mcpath))

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'New profile would have been generated, property list follows: {0}'.format(content)
        ret['changes'] = {name: 'need to make profile'}
        return ret

    success = __salt__['profile.install'](mcpath)
    ret['result'] = success
    if success:
        ret['comment'] = 'Profile "{0}", installed successfully.'.format(name)
        ret['changes'].update({name: {'Old Profile': valid['old_payload'],
                                        'New Profile': valid['new_payload']}})
    else:
        ret['comment'] = 'Failed to install profile with identifier: "{0}"'.format(name)
        return ret

    return ret


def absent(name):
    '''
    Remove the configuration profile with the specified identifier.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    exists = __salt__['profile.exists'](name)

    if not exists:
        ret['comment'] = 'Profile is already absent'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Profile with identifier: {0} would have been removed.'.format(name)
        return ret

    success = __salt__['profile.remove'](name)

    if success:
        ret['comment'] = 'Profile with identifier: {0} successfully removed'.format(name)
        ret['changes'].update({name: {'old': 'Installed',
                                      'new': 'Removed'}})
    else:
        ret['result'] = False
        ret['comment'] = 'Failed to remove profile with identifier: {0}'.format(name)

    return ret
