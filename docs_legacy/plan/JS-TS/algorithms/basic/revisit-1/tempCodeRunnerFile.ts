function validPalindrome2(s: string): boolean {
    
    // Set outermost left-and-right length
    let left = 0;
    let right = s.length -1;

    // no matter ValindPalindrome or isPalindromeInRange
    // they share the same logic on iteration of 
    // left ++ and right --, while s[left] === s[right]
    // The extra layer is the deletion logic (skip left => skip right) 
    // You'll see it soon below:
    while (left < right) {
        if (s[left] === s[right]) {
            left ++;
            right --;

        } else {
            return isPalindromeInRange2(s, left + 1, right) 
            || isPalindromeInRange2(s, left, right - 1);
        }
    }
return true;
}

function isPalindromeInRange2(s: string, left: number, right: number): boolean {
    while (left < right) {
        if (s[left] === s[right]) {
            left ++;
            right --;
        } else {
            return false;
        }
        
    }
    return true;
}

console.log(validPalindrome2('acbba'));
console.log(validPalindrome2('abc'));
console.log(validPalindrome2('abba'));