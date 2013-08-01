"""Generate backupset configuration files"""

import sys
from holland.cli.cmd.interface import ArgparseCommand, argument
from holland.core import Config, load_plugin, BackupPlugin
from holland.core.plugin import PluginError, plugin_registry

@plugin_registry.register
class MakeConfig(ArgparseCommand):
    """Generate a new config"""

    name = 'mk-config'
    aliases = ['mc']
    summary = "Generate a configuration file from a plugin"
    description = """
    Generate a configuration file from a plugin
    """

    arguments = [
        argument('--file', default='-'),
        argument('--name', help="Base name of the configuration to generate"),
        argument('--minimal', action='store_true'),
        argument('--edit', action='store_true'),
        argument('plugin')
    ]

    def execute(self, namespace, parser):
        """Run the mkconfig command"""
        try:
            plugin = load_plugin('holland.backup', namespace.plugin)
        except PluginError, exc:
            self.stderr("%s", exc)
            return 1

        config = Config.from_string("""
        [holland:backup]
        plugin = %s
        """ % namespace.plugin)
        config = plugin.base_configspec().validate(config)

        plugin.configspec().validate(config)

        if namespace.edit:
            self.stderr("Edit is not supported")
            return 1

        if namespace.file == '-':
            namespace.file = sys.stdout
        try:
            config.write(namespace.file)
        except IOError, exc:
            self.stderr("Failed to write config file: %s", exc)
            return 1
        return 0

    def plugin_info(self):
        """Provide plugin_info for mkconfig"""
        return dict(
            name='mk-config',
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
