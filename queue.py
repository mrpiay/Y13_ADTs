# Function to initialize the circular queue
def qInit():
    global qSize, qData, qFront, qRear, qCount
    qSize = 4  # The maximum size of the queue
    qData = []  # List to hold the queue elements
    # Initialize the queue with default placeholder values
    for i in range(qSize):
        qData.append('-')
    qFront = 0  # Points to the front element of the queue
    qRear = -1  # Points to the last element of the queue; -1 indicates the queue is empty
    qCount = 0  # Number of elements currently in the queue

# Function to check if the queue is empty
def qEmpty():
    return qCount == 0  # Returns True if the queue is empty, False otherwise

# Function to check if the queue is full
def qFull():
    return qCount == qSize  # Returns True if the queue is full, False otherwise

# Function to print the current elements of the queue
def qPrint():
    if qEmpty():
        print("Queue is empty")  # Message when the queue is empty
    else:
        current = qFront  # Start from the front of the queue
        # Loop through the number of elements in the queue
        for i in range(qCount):
            print(qData[current])  # Print the current element
            current = (current + 1) % qSize  # Move to the next element (circularly)

# Function to add a value to the rear of the queue
def qAdd(value):
    global qRear, qCount

    if qFull():
        print("Queue is full")  # Message when the queue is full
    else:
        # Move the rear pointer to the next position (circularly)
        qRear = (qRear + 1) % qSize
        qData[qRear] = value  # Add the new value at the rear
        qCount = qCount + 1  # Increment the count of elements in the queue

# Function to remove a value from the front of the queue
# Returns the removed value, or None if the queue was empty
def qRemove():
    global qFront, qCount

    if qEmpty():
        print("Queue is empty")  # Message when the queue is empty
        return None
    else:
        qFrontValue = qData[qFront]  # Save the front value before it is overwritten
        qData[qFront] = '-'  # Reset the front position to the default placeholder
        # Move the front pointer to the next position (circularly)
        qFront = (qFront + 1) % qSize
        qCount = qCount - 1  # Decrement the count of elements in the queue
        return qFrontValue  # Return the removed value
