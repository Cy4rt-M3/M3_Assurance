from abc import ABC, abstractmethod


class AudienceProfile(ABC):

    name = "base"

    @abstractmethod
    def allowed_sections(self):
        pass

    @abstractmethod
    def hidden_sections(self):
        pass

    @abstractmethod
    def report_title(self):
        pass