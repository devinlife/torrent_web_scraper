class BoardPageIterator:
    def __init__(self, web_addr, start_index, remains):
        self.__web_addr = web_addr
        self.__web_index = start_index - 1
        self.__remains = remains
        self.__early_stop = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.__remains <= 0:
            raise StopIteration
        if self.__early_stop:
            raise StopIteration

        self.__remains -= 1
        self.__web_index += 1

        "return url index"
        url = "%s%s" % (self.__web_addr, self.__web_index)
        # print("DEBUG : %s" % url)
        return url

    def mark_for_early_stop(self):
        self.__early_stop = True
