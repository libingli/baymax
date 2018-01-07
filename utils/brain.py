# -*- coding: utf-8-*-
import logging
import pkgutil
import sys

sys.path.append("..")
from skills import chat

class Brain(object):

    def __init__(self, mic):
        """
        Instantiates a new Brain object, which cross-references user
        input with a list of skills. Note that the order of brain.skills
        matters, as the Brain will cease execution on the first skill
        that accepts a given input.

        Arguments:
        mic -- used to interact with the user (for both input and output)
        """

        self.mic = mic
        self.handling = False
        self.logger = logging.getLogger(__name__)
        self.skills = self.learn_skills()

    def learn_skills(self):
        """
        Dynamically loads all the skills in the skills folder and sorts
        them by the PRIORITY key. If no PRIORITY is defined for a given
        skill, a priority of 0 is assumed.
        """

        locations = [
           "/home/li/baymax/skills" 
        ]
        self.logger.info("Looking for skills in: %s",
                     ', '.join(["'%s'" % location for location in locations]))
        skills = []
        # skills that are not allow to be call via Wechat or Email
        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                mod = loader.load_module(name)
            except Exception as e:
                self.logger.error("Skipped skill '%s' due to an error %s.", name, e)
            else:
                if hasattr(mod, 'WORDS'):
                    self.logger.info("Found skill '%s' with words: %r", name, mod.WORDS)
                    skills.append(mod)
                else:
                    self.logger.info("Skipped skill '%s' because it misses " +
                                   "the WORDS constant.", name)
        skills.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY')
                     else 0, reverse=True)
        return skills

    def determine(self, text):
        """
        Passes user input to the appropriate skill, testing it against
        each candidate skill's isValid function.

        Arguments:
        text -- user input, typically speech, to be parsed by a skill
        """
        for skill in self.skills:
            if skill.isValid(text):
                try:
                    self.handling = True
                    skill.handle(text, self.mic)
                    self.handling = False
                except Exception as e:
                    self.logger.error("Handling of phrase '%s' by " +
                        "skill '%s' error: %s", text, skill.__name__, e)
                    reply = "抱歉，我的大脑出故障了，晚点再试试吧"
                    self.mic.say(reply)
                else:
                    self.logger.info("Handling of phrase '%s' by " +
                                       "skill '%s' completed", text,
                                       skill.__name__)
                finally:
                    return True
        self.logger.debug("No skill was able to handle the phrases: %s", text)
        chat.handle(text, self.mic)
        return False
