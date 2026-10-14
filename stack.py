# Function to initialize the stack
def sInit():
    global sSize, sData, sTop
    sSize = 40  # The maximum size of the stack
    sData = []  # List to hold stack elements
    # Initialize the stack with default placeholder values
    for i in range(sSize):
        sData.append('-')
    sTop = -1  # Index of the topmost element in the stack; -1 indicates the stack is empty

# Function to check if the stack is empty
def sEmpty():
    return sTop == -1  # Returns True if the stack is empty, False otherwise

# Function to check if the stack is full
def sFull():
    return sTop == sSize - 1  # Returns True if the stack is full, False otherwise

# Function to print the current elements of the stack
def sPrint():
    if sEmpty():
        print("Stack is empty")  # Message when the stack is empty
    else:
        # Print the stack elements from top to bottom
        for i in range(sTop + 1):
            print(sData[sTop - i])  # Reverse order for proper stack representation

# Function to push a value onto the stack
def sPush(value):
    global sTop
    if sFull():
        print("Stack is full")  # Message when the stack is full
    else:
        sTop = sTop + 1  # Move the top index up by one
        sData[sTop] = value  # Add the new value at the top of the stack

# Function to pop the top value from the stack
def sPop():
    global sTop
    if sEmpty():
        print("Stack is empty")  # Message when the stack is empty
    else:
        sTopValue = sData[sTop]  # Retrieve the topmost value
        sTop = sTop - 1  # Move the top index down by one
        return sTopValue  # Return the popped value

# Function to peek at the top value of the stack without removing it
def sPeek():
    if sEmpty():
        print("Stack is empty")  # Message when the stack is empty
    else:
        return sData[sTop]  # Return the topmost value
