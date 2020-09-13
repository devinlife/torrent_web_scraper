class BoardItemIterator:
    def __init__(self, board_item_list):
        self.__item_list = board_item_list
        self.__early_stop = False

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.__item_list) <= 0:
            raise StopIteration
        if self.__early_stop:
            raise StopIteration

        poped = self.__item_list.pop(0)

        '''return을 2개(title, href)를 해야함.'''
        # __item_list가 리스트의 리스트이므로 poped를 return 하면 됨
        return poped

    def mark_for_early_stop(self):
        self.__early_stop = True
