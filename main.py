import stack as s
import queue as q
import linked_list as l
import binary_tree as b

def test_stack():
    s.sInit()
    for i in range(5):
        s.sPush(i)
    s.sPrint()
    print()
    for i in range(2):
        print(s.sPop())
    print()
    s.sPrint()
    print()
    print(s.sPeek())

def test_queue():
    q.qInit()
    for i in range(5):
        q.qAdd(i)
    q.qPrint()
    print()
    for i in range(2):
        q.qRemove()
    q.qPrint()

def test_list():
    l.lInit()
    for i in range(l.lSize + 1):
        l.lInsert(i, 0)
    l.lPrint()
    print()
    
    l.lInit()
    for i in range(l.lSize + 1):
        l.lInsert(i, 1)
    l.lPrint()
    print()

    l.lInit()
    for i in range(l.lSize + 1):
        l.lInsert(i, 2)
    l.lPrint()
    print()

    l.lRemove(2)
    l.lRemove(1)
    l.lPrint()
    
    l.lSearch(0)
    l.lSearch(3)
    l.lSearch(-1)

def test_tree():
    b.bInit()
    b.bInsert(5)
    b.bInsert(7)
    b.bInsert(3)
    b.bInsert(1)
    b.bInsert(9)
    b.bInsert(0)
    print(b.bData)    
    print(b.bRight)    
    print(b.bLeft)    
    b.bSearch(1)
    b.bSearch(9)
    b.bSearch(-1)
    
def testAll():
    test_stack()
    print()
    test_queue()
    print()
    test_list ()
    print()
    test_tree()
# testAll()

def reverseString(string):
    s.sInit()  # Initialize the stack
    for char in string:
        s.sPush(char)  # Push each character onto the stack
    reversedString = ""
    while not s.sEmpty():
        reversedString += s.sPop()  # Pop each character and build the reversed string
    return reversedString

# Example usage:
# print(reverseString("hello"))

def isBalancedParentheses(expression):
    s.sInit()  # Initialize the stack
    for char in expression:
        if char == "(":
            s.sPush(char)  # Push open parentheses onto the stack
        elif char == ")":
            if s.sEmpty():  # Stack is empty, no matching open parentheses
                return False
            s.sPop()  # Pop the matching open parentheses
    return s.sEmpty()  # If the stack is empty, parentheses are balanced

# Example usage:
# print(isBalancedParentheses("(())"))  # Output: True
# print(isBalancedParentheses("(()"))   # Output: False

def qPeek():
    if q.qEmpty():
        print("Queue is empty")
        return None
    return q.qData[q.qFront]

# Example usage:
# q.qInit()
# q.qAdd(10)
# q.qAdd(20)
# print(qPeek())

def lCount():
    count = 0
    current = l.lStart
    while current != -1:
        count += 1
        current = l.lLinks[current]
    return count

# Example usage:
# l.lInit()
# l.lInsert(1)
# l.lInsert(2)
# print(lCount())

def lReverse():
    prev = -1
    current = l.lStart
    while current != -1:
        nextNode = l.lLinks[current]
        l.lLinks[current] = prev
        prev = current
        current = nextNode
    l.lStart = prev

# Example usage:
# l.lInit()
# for i in range(10):
#     l.lInsert(i)
# l.lPrint()
# lReverse()
# print()
# l.lPrint()  
    
# The leftmost node holds the minimum value (it is not necessarily a leaf:
# it may still have a right child)
def bFindMin():
    if b.bEmpty():
        print("Tree is empty")
    else:
        current = b.bRoot
        while b.bLeft[current] != -1:
            current = b.bLeft[current]
        print("Minimum value:", b.bData[current])

# Example usage:
# b.bInit()
# b.bInsert(10)
# b.bInsert(5)
# b.bInsert(15)
# bFindMin()

# The rightmost node holds the maximum value
def bFindMax():
    if b.bEmpty():
        print("Tree is empty")
    else:
        current = b.bRoot
        while b.bRight[current] != -1:
            current = b.bRight[current]
        print("Maximum value:", b.bData[current])

# Example usage:
# b.bInit()
# b.bInsert(10)
# b.bInsert(5)
# b.bInsert(15)
# bFindMax()

# Only run the examples when this file is executed directly, not when it is imported
if __name__ == "__main__":
    b.bInit()
    b.bInsert(10)
    b.bInsert(5)
    b.bInsert(15)
    bFindMin()
    bFindMax()
