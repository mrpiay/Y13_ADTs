# Function to initialize the linked list
def lInit():
    global lSize, lData, lLinks, lStart, lFree
    lSize = 40  # The maximum size of the linked list
    lData = []  # List to store data values for each node
    lLinks = []  # List to store links (next node indices) for each node
    # Initialize data list with default placeholder values ('-')
    for i in range(lSize):
        lData.append('-')
    # Initialize links list, linking each node to the next one
    for i in range(lSize):
        lLinks.append(i + 1)
    lLinks[lSize - 1] = -1  # The last node points to -1 (end of the free list)
    lStart = -1  # Start of the linked list, -1 indicates the list is empty
    lFree = 0  # Points to the first free node (start of the free list)

# Function to check if the linked list is empty
def lEmpty():
    return lStart == -1  # Returns True if the list is empty, False otherwise

# Function to check if the linked list is full
def lFull():
    return lFree == -1  # Returns True if there are no free nodes left

# Function to allocate a new node from the free list
def lAllocateNode(value):
    global lFree
    newNode = lFree  # Get the index of the first free node
    lData[lFree] = value  # Assign the value to the new node
    lFree = lLinks[lFree]  # Update the free pointer to the next free node
    return newNode  # Return the index of the newly allocated node

# Function to release a node back to the free list
def lReleaseNode(node):
    global lFree
    lData[node] = "-"  # Reset the node's data to the default placeholder
    lLinks[node] = lFree  # Point the released node to the current start of the free list
    lFree = node  # Update the free pointer to the released node

# Function to search for a value in the linked list
# Returns the index of the node holding the value, or -1 if it is not in the list
def lSearch(value, delete=False):
    global lStart, lFree
    if lEmpty():
        print("List is empty")  # Message when the list is empty
        return -1
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
            return -1
        elif not delete:
            print(value, "found at position", current)  # Value found and no deletion
        else:
            # Handle node deletion
            if prev == -1:  # If the node to delete is the first node
                lStart = lLinks[current]
            else:
                lLinks[prev] = lLinks[current]  # Skip the current node
            lReleaseNode(current)  # Release the deleted node back to the free list
        return current  # Index of the node that was found (or removed)

# Function to remove a node with the specified value
# Returns the index of the removed node, or -1 if the value was not found
def lRemove(value):
    return lSearch(value, True)  # Search and delete the node with the given value

# Function to insert a value into the linked list
def lInsert(value, mode=0):
    '''
    Insert a value into the linked list based on the mode:
    0 - Insert at the start.
    1 - Insert in ascending order.
    2 - Insert in descending order.
    '''
    global lStart, lFree
    if lFull():
        print("List is full")  # Message when the list is full
    else:
        newNode = lAllocateNode(value)  # Allocate a new node
        prev = -1  # Keeps track of the previous node
        current = lStart  # Start searching from the first node
        nodeFound = False
        # Traverse the list to find the appropriate position for insertion
        # (mode 0 always inserts at the start, so it skips the traversal)
        while mode != 0 and current != -1 and not nodeFound:
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
