# Function to initialize the linked list
def lInit():
    global lSize, lData, lLinks, lStart, lHeap
    lSize = 40  # The maximum size of the linked list
    lData = []  # List to store data values for each node
    lLinks = []  # List to store links (next node indices) for each node
    # Initialize data list with default placeholder values ('-')
    for i in range(lSize):
        lData.append('-')
    # Initialize links list, linking each node to the next one
    for i in range(lSize):
        lLinks.append(i + 1)
    lLinks[lSize - 1] = -1  # The last node points to -1 (end of the heap)
    lStart = -1  # Start of the linked list, -1 indicates the list is empty
    lHeap = 0  # Points to the first free node in the heap

# Function to check if the linked list is empty
def lEmpty():
    return lStart == -1  # Returns True if the list is empty, False otherwise

# Function to check if the linked list is full
def lFull():
    return lHeap == -1  # Returns True if there are no free nodes left

# Function to allocate a new node from the heap
def lAllocateNode(value):
    global lHeap
    newNode = lHeap  # Get the index of the first free node
    lData[lHeap] = value  # Assign the value to the new node
    lHeap = lLinks[lHeap]  # Update the heap pointer to the next free node
    return newNode  # Return the index of the newly allocated node

# Function to release a node back to the heap
def lReleaseNode(node):
    global lHeap
    lData[node] = "-"  # Reset the node's data to the default placeholder
    lLinks[node] = lHeap  # Point the released node to the current heap start
    lHeap = node  # Update the heap pointer to the released node

# Function to search for a value in the linked list
def lSearch(value, delete=False):
    global lStart, lHeap
    if lEmpty():
        print("List is empty")  # Message when the list is empty
    else:
        prev = -1  # Keeps track of the previous node
        current = lStart  # Start searching from the first node
        nodeFound = False
        # Traverse the list until the value is found or end is reached
        while current != -1 and not nodeFound:
            if lData[current] == value:
                nodeFound = True  # Value found
            else:
                prev = current
                current = lLinks[current]
        if not nodeFound:
            print(value, "not found")  # Value not found in the list
        elif not delete:
            print(value, "found at position", current)  # Value found and no deletion
        else:
            # Handle node deletion
            if prev == -1:  # If the node to delete is the first node
                lStart = lLinks[current]
            else:
                lLinks[prev] = lLinks[current]  # Skip the current node
            lReleaseNode(current)  # Release the deleted node back to the heap

# Function to remove a node with the specified value
def lRemove(value):
    lSearch(value, True)  # Search and delete the node with the given value

# Function to insert a value into the linked list
def lInsert(value, mode=0):
    '''
    Insert a value into the linked list based on the mode:
    0 - Insert at the start.
    1 - Insert in ascending order.
    2 - Insert in descending order.
    '''
    global lStart, lHeap
    if lFull():
        print("List is full")  # Message when the list is full
    else:
        newNode = lAllocateNode(value)  # Allocate a new node
        prev = -1  # Keeps track of the previous node
        current = lStart  # Start searching from the first node
        nodeFound = False
        # Traverse the list to find the appropriate position for insertion
        while current != -1 and not nodeFound:
            if (mode == 1 and lData[current] > value) or (mode == 2 and lData[current] < value):
                nodeFound = True  # Found the position for insertion
            else:
                prev = current
                current = lLinks[current]
        if mode == 0 or prev == -1:  # Insert at the start or as the first node
            lLinks[newNode] = lStart
            lStart = newNode
        else:  # Insert at the appropriate position
            lLinks[newNode] = current
            lLinks[prev] = newNode

# Function to print the linked list
def lPrint():
    global lStart
    if lEmpty():
        print("List is empty")  # Message when the list is empty
    else:
        current = lStart  # Start from the first node
        while current != -1:
            nextNode = lLinks[current]  # Get the next node index
            if nextNode != -1:
                print(lData[current], "->", lData[nextNode])  # Print current -> next
            else:
                print(lData[current], "-> -1")  # End of the list
            current = nextNode  # Move to the next node
