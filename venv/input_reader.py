from typing import List, Tuple


class InputReader:
    def __init__(self):
        self.user_input = []

    def read_val(self, message: str = "", default = None):
        """
        Reads a generic value from the console. This function should be used instead of the normal input, so that the
        input is saved and shown in the end to the user.
        :param message: Message to be shown as question for the input
        :param default: The default value that will be used if the user presses enter
        :return: The value read
        """
        val = input(message + ("(Enter for {})".format(default) if default else "") + "\n")
        if default and val == "":
            val = default
        self.user_input.append(val)
        return val

    def read_yesno(self, question: str) -> bool:
        """
        Reads a yes or no value from the console and returns the corresponding value as a boolean.
        This function loops while an incorrect value is given
        :param question: The question to be made to the user
        :return: True or False corresponding to yes or no
        """
        final_question = question + "(y/n)" + "\n"
        val = input(final_question)

        while val != "y" and val != "n":
            val = input(final_question)

        self.user_input.append(val)
        return val == "y"

    def read_from_options(self, question: str, options: List[str]) -> str:
        """
        Reads a value from a specific set of options given as a parameter
        :param question: The question to be made to the user
        :param options: The available options
        :return: The value the user typed
        """
        joined_options = "({})".format("/".join(options))
        final_question = question + joined_options + "\n"
        val = input(final_question)

        while val not in options:
            val = input(final_question)

        self.user_input.append(val)
        return val

    def read_int(self, question: str = "") -> int:
        """
        Reads an int from the console. This function keeps prompting for a value until a valid int is provided
        :param question: The question to be made to the user
        :return: A valid int
        """
        val = None

        while val is None:
            try:
                val = int(input(question + "\n"))
            except ValueError:
                val = None

        self.user_input.append(str(val))
        return val

    def all_given_input(self) -> List[str]:
        """
        Returns all the given user input throughout the program.
        This is useful to allow the user to run the program and input the same options
        :return: All the input that user typed in
        """
        return self.user_input
