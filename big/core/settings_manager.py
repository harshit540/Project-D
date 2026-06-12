from database.models import SettingsRepository

class SettingsManager:
    @staticmethod
    def get_theme():
        return SettingsRepository.get("theme", "Dark")

    @staticmethod
    def set_theme(theme_name):
        SettingsRepository.set("theme", theme_name)

    @staticmethod
    def get_notifications_enabled():
        return SettingsRepository.get("global_notifications", True)

    @staticmethod
    def set_notifications_enabled(enabled):
        SettingsRepository.set("global_notifications", enabled)

    @staticmethod
    def get_startup_sync_enabled():
        return SettingsRepository.get("startup_sync", False)

    @staticmethod
    def set_startup_sync_enabled(enabled):
        SettingsRepository.set("startup_sync", enabled)