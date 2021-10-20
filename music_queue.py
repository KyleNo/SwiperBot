import random

class Node:
  def __init__(self, url: str, title: str, channel):
    self.url = url
    self.title = title
    self.channel = channel
    self.next = None

# TODO: make sure self.tail doesnt get mangled in remove and shuffle functions
class Music_Queue:
  def __init__(self):
    self.head = None
    self.tail = None
    self.length = 0

  def add(self, node: Node):
    if self.head is None:
      self.head = node
      self.tail = node
    else:
      self.tail.next = node
      self.tail = node
    self.length += 1
  
  def peek(self) -> Node:
    return self.head

  def clear(self):
    self.head = None
    self.tail = None
    self.length = 0

  def getNext(self) -> Node:
    if self.head is None:
      print("Err: Tried to get next from empty queue")
      return None
    res = self.head
    self.head = self.head.next
    if self.head is None:
      self.tail = None
    self.length -= 1
    return res

  def hasNext(self):
    return self.head is not None

  def getQueue(self) -> list:
    res = []
    node = self.head
    while node is not None:
      res.append(node)
      node = node.next
    return res

  # Remove the ith song from the queue
  def remove(self, i: int):
    if i >= self.length:
      print("Err: Remove index out of range")
      return None
    curr = 0
    node = self.head
    prev = None
    while node is not None:
      if curr == i:
        if prev:
          prev.next = node.next
          if node.next is None:
            self.tail = prev
        else:
          self.head = node.next
          if node.next is None:
            self.tail = None
        self.length -= 1
        return node
      prev = node
      node = node.next
      curr += 1
    return None 
  #def _moveBack(self, source, dest):
  #def _moveForw(self, source, dest):
  #def move(self, source, dest):

  # shuffles queue from index start (inclusive) to index end (exclusive)
  #     (zero-indexed)
  # end - start = number of elements being shuffled
  def shuffle(self, start=0, end=None):
    if end==None:
      end = self.length
    curr = self.head
    before = curr
    count = 0
    shuff = []
    fromZero = False
    if start==0:
      fromZero = True
    while count < start:
      before = curr
      curr = curr.next
      count += 1
    while count < end:
      shuff.append(curr)
      curr = curr.next
      count += 1
    after = curr
    random.shuffle(shuff)
    curr = shuff.pop()
    if fromZero:
      self.head = curr
    else:
      before.next = curr
    prev = curr
    while len(shuff)>0:
      curr = shuff.pop()
      prev.next = curr
      prev = curr
    curr.next = after
    if after is None:
      self.tail = curr


