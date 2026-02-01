// A1. The shortest subarray length ≥ target

// Given an array nums of positive integers and a positive integer target,
// return the length of the shortest contiguous subarray whose sum is at least target.
// If no such subarray exists, return 0.

// Example:
// Input: nums = [2,3,1,2,4,3], target = 7
// Output: 2 (the subarray [4,3] has sum 7 and length 2, which is minimal)

// -----------------------------------------------------------------------------
// 1) sum = target 
// -----------------------------------------------------------------------------

function shortestSubarray_Equal(nums: number[], target: number): number {

    let left = 0;
    let sum = 0;
    let shortestLength = Infinity;

    for (let right = 0; right < nums.length; right++) {
        sum += nums[right]!;

        // reduce the sum to a number less than target
        while (sum > target) {
            sum -= nums[left]!;
            left++;
        }

        if (sum === target) {
            const currentLength = right - left + 1;
            shortestLength = Math.min(shortestLength, currentLength);
        }
    }
    return shortestLength;
}

console.log(shortestSubarray_Equal([1,2,3,4],3));   // 1
console.log(shortestSubarray_Equal([1,5,2,1,4],3)); // 2

// -----------------------------------------------------------------------------
// 2) sum >= target + return all shortest length subarrays
// -----------------------------------------------------------------------------

function shortestSubarray_GreaterorEqual(nums: number[], target: number): number[][] {
  let left = 0;
  let sum = 0;
  let shortestLength = Infinity;
  const results: number[][] = [];

  for (let right = 0; right < nums.length; right++) {
    sum += nums[right]!;

    while (sum >= target) {
      const currentLength = right - left + 1;

      if (currentLength < shortestLength) {
        shortestLength = currentLength;
        results.length = 0; // 清空旧结果
        results.push(nums.slice(left, right + 1));
      } else if (currentLength === shortestLength) {
        results.push(nums.slice(left, right + 1));
      }

      sum -= nums[left]!; // 记得从 sum 中减去左端
      left++;
    }
  }

  return results;
}

console.log(shortestSubarray_GreaterorEqual([1,2,3,4],3)); 
console.log(shortestSubarray_GreaterorEqual([1,4,1],5)); 