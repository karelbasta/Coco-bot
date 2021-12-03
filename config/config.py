"""Configarution load module

This module loads the configuration from configuration file.
Returns object of Config class.
"""
import json
import sys

from colorama import init, Fore

init(autoreset=True)


class Config:
    """Config class

    This class loads the configuration from configuration file.
    Returns object of Config class.
    """

    def _get(self, group: str, key: str = None) -> str:
        """Get the value of group or key in group

        If value is not present in configuration file, default value is returned.
        If key is not present in neither configuration file nor default file, None is returned.
        """
        if key is None:
            if group in self.config:
                return self.config[group]
            if group in self.default:
                return self.default[group]
            return None
        if group in self.config and key in self.config[group]:
            return self.config[group][key]
        if group in self.default and key in self.default[group]:
            return self.default[group][key]
        return None

    def __init__(self) -> None:
        """Initialize the Config class"""
        try:
            with open("config/config.json", "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)
            with open("config/default.json", "r", encoding="utf-8") as default_file:
                self.default = json.load(default_file)
        except FileNotFoundError:
            print("Configuration file not found.")
            sys.exit(1)

        self.prefixes = self._get("bot", "prefixes")
        self.extensions_enabled = self._get("extensions", "enabled")
        print(f"{Fore.YELLOW}Enabled extensions: " + ", ".join(self.extensions_enabled))
        self.extensions_disabled = self._get("extensions", "disabled")
        print(
            f"{Fore.YELLOW}Disabled extensions: " + ", ".join(self.extensions_disabled)
        )

    @property
    def bot_token(self) -> str:
        """Get the bot token"""
        return self._get("bot", "token")

    @property
    def bot_owner(self) -> str:
        """Get the bot owner"""
        return self._get("bot", "owner")

    @property
    def bot_log_channel_id(self) -> str:
        """Get the bot log channel"""
        return self._get("bot", "log_channel_id")

    @property
    def color(self) -> str:
        """Get the color"""
        return self._get("bot", "color")

    @property
    def logo_url(self) -> str:
        """Get the logo url"""
        return self._get("bot", "logo_url")

    @property
    def debug(self) -> bool:
        """Get the debug mode"""
        return self._get("bot", "debug") == "True"

    @property
    def reddit(self) -> dict:
        """Get the reddit configuration"""
        return self._get("reddit")

    @property
    def openai(self) -> dict:
        """Get the openai configuration"""
        return self._get("openai")

    def reload(self) -> None:
        """Reload the configuration"""
        self.__init__()

    def save(self) -> None:
        """Save the configuration"""
        if not self.config.get("bot").get("prefixes"):
            self.config["bot"]["prefixes"] = self.prefixes
        with open("config.json", "w", encoding="utf-8") as config_file:
            json.dump(self.config, config_file, indent=4)

    def enable_extension(self, extension: str) -> None:
        """Enable extension"""
        if extension in self.extensions_disabled:
            self.extensions_disabled.remove(extension)
            self.extensions_enabled.append(extension)
            self.save()
        elif extension in self.extensions_enabled:
            print("Extension is already enabled.")
        else:
            print("Extension {extension} not found")

    def disable_extension(self, extension: str) -> None:
        """Disable extension"""
        if extension in self.extensions_enabled:
            self.extensions_enabled.remove(extension)
            self.extensions_disabled.append(extension)
            self.save()
        elif extension in self.extensions_disabled:
            print("Extension is already disabled.")
        else:
            print("Extension {extension} not found")


config = Config()
