""" Given a string s, return the longest palindromic substring in s.

 

Example 1:

Input: s = "babad"
Output: "bab"
Explanation: "aba" is also a valid answer.
Example 2:

Input: s = "cbbd"
Output: "bb"
 

Constraints:

1 <= s.length <= 1000
s consist of only digits and English letters. """
class Solution(object):
    def longestPalindrome(self, s):
        def is_palindrome(sub):
            return sub == sub[::-1]

        longest = ""

        for i in range(len(s)):
            for j in range(i, len(s)):
                if j - i + 1 <= len(longest):
                    continue

                sub = s[i:j+1]
                if is_palindrome(sub):
                    longest = sub

        return longest
s = Solution()
print(s.longestPalindrome("babad"))