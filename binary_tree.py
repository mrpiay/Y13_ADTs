# Function to initialize the binary tree
def bInit():
    global bSize, bData, bLeft, bRight, bRoot, bHeap
    bSize = 10  # Maximum number of nodes in the tree
    bRoot = -1  # Index of the root node, -1 indicates the tree is empty
    bHeap = 0  # Index of the first available free node in the heap
    bData = []  # List to store data values for each node
    bRight = []  # List to store the right child index for each node
    bLeft = []  # List to store the left child index for each node
    
    # Initialize data list with default placeholder values ('-')
    for i in range(bSize):
        bData.append('-')
    # Initialize left and right child lists
    for i in range(bSize):
        bRight.append(-1)  # Initially, no right child for any node
        bLeft.append(i + 1)  # Each node points to the next as a free node
    bLeft[bSize - 1] = -1  # The last node in the heap points to -1 (end of heap)

# Function to check if the binary tree is empty
def bEmpty():
    return bRoot == -1  # Returns True if the tree has no root node

# Function to check if the binary tree is full
def bFull():
    return bHeap == -1  # Returns True if there are no free nodes left in the heap

# Function to allocate a new node from the heap
def bAllocateNode(value):
    global bHeap, bRight, bLeft
    newNode = bHeap  # Get the index of the first free node
    bData[bHeap] = value  # Assign the value to the new node
    bHeap = bLeft[bHeap]  # Update the heap pointer to the next free node
    bLeft[newNode] = -1  # Initialize the left child of the new node as -1
    bRight[newNode] = -1  # Initialize the right child of the new node as -1
    return newNode  # Return the index of the newly allocated node

# Function to search for a value in the binary tree
def bSearch(value):
    global bRoot, bHeap
    if bEmpty():
        print("Tree is empty")  # Message when the tree is empty
    else:
        current = bRoot  # Start from the root node
        nodeFound = False
        # Traverse the tree to find the value
        while current != -1 and not nodeFound:
            if bData[current] == value:  # Value found
                nodeFound = True
            elif value < bData[current]:  # Move to the left child
                current = bLeft[current]
            else:  # Move to the right child
                current = bRight[current]
        if not nodeFound:
            print(value, "not found")  # Value not found in the tree
        else:
            print(value, "found at position", current)  # Value found

# Function to insert a value into the binary tree
def bInsert(value):
    global bRoot, bHeap
    if bFull():
        print("Tree is full")  # Message when the tree is full
    else:
        newNode = bAllocateNode(value)  # Allocate a new node
        if bEmpty():
            bRoot = newNode  # If tree is empty, make the new node the root
        else:
            current = bRoot  # Start from the root node
            parent = -1  # Keeps track of the parent node
            # Traverse the tree to find the correct position for insertion
            while current != -1:
                parent = current
                if value < bData[current]:  # Move to the left child
                    current = bLeft[current]
                else:  # Move to the right child
                    current = bRight[current]
            # Insert the new node as the left or right child of the parent
            if value < bData[parent]:
                bLeft[parent] = newNode
            else:
                bRight[parent] = newNode
