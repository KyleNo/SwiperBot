class Node:
  def __init__(self, url: str, title: str, channel):
    self.url = url
    self.title = title
    self.channel = channel
    self.next = None


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