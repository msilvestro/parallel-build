class Logger:
    output_function = print

    @classmethod
    def log(cls, text):
        cls.output_function(text)
