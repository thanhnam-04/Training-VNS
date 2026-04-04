""" Given a signed 32-bit integer x, return x with its digits reversed. If reversing x causes the value to go outside the signed 32-bit integer range [-231, 231 - 1], then return 0.

Assume the environment does not allow you to store 64-bit integers (signed or unsigned).

 

Example 1:

Input: x = 123
Output: 321
Example 2:

Input: x = -123
Output: -321
Example 3:

Input: x = 120
Output: 21
  """
class Solution(object):
    def reverse(self, x):
        sign = -1 if x < 0 else 1
        x *= sign
        
        reversed_num = 0
        while x:
            reversed_num = reversed_num * 10 + x % 10
            x //= 10
        
        reversed_num *= sign
        
        if reversed_num < -2**31 or reversed_num > 2**31 - 1:
            return 0
        
        return reversed_num
s = Solution()
print(s.reverse(-123))