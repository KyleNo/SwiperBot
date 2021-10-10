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
        else:
          self.head = node.next
        self.length -= 1
        return node
      prev = node
      node = node.next
      curr += 1
    return None

  #def moveBack(self, source, dest):
  #
