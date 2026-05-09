def secondLargest(arr):
    n =len(arr)

    sorted = arr.sort()
    

    for i in range(n-2,-1,-1):

        if arr[i] != arr[n-1]:
            return arr[i]
        
    return -1


arr = [10,20,56,100,100,100,97] # 10,20,56,97,100,100,100
print(secondLargest(arr))


sorted = arr.sort()
print(sorted)



# looking for the third largest

# O(n log n)

def thirdLargest(arr):
    n = len(arr)

    #set all variables to - inf

    first = float('-inf')
    second = float('-inf')
    third = float('-inf')

    if n < 3:
        return -1
    
    for i in range(n):

        if (arr[i] > first):
            third = second
            second = first
            first = arr[i]

       

           

        
        
