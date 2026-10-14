# Function to initialize the binary tree
def bInit():
    global bSize, bData, bLeft, bRight, bRoot, bFree
    bSize = 10  # Maximum number of nodes in the tree
    bRoot = -1  # Index of the root node, -1 indicates the tree is empty
    bFree = 0  # Index of the first free node (start of the free list)
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
    bLeft[bSize - 1] = -1  # The last free node points to -1 (end of the free list)

# Function to check if the binary tree is empty
def bEmpty():
    return bRoot == -1  # Returns True if the tree has no root node

# Function to check if the binary tree is full
def bFull():
    return bFree == -1  # Returns True if there are no free nodes left

# Function to allocate a new node from the free list
def bAllocateNode(value):
    global bFree, bRight, bLeft
    newNode = bFree  # Get the index of the first free node
    bData[bFree] = value  # Assign the value to the new node
    bFree = bLeft[bFree]  # Update the free pointer to the next free node
    bLeft[newNode] = -1  # Initialize the left child of the new node as -1
    bRight[newNode] = -1  # Initialize the right child of the new node as -1
    return newNode  # Return the index of the newly allocated node

# Function to search for a value in the binary tree
# Returns the index of the node holding the value, or -1 if it is not in the tree
def bSearch(value):
    global bRoot, bFree
    if bEmpty():
        print("Tree is empty")  # Message when the tree is empty
        return -1
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
            return -1
        else:
            print(value, "found at position", current)  # Value found
            return current

# Function to insert a value into the binary tree
def bInsert(value):
    global bRoot, bFree
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
