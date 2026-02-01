
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

console.log(shortestSubarray_GreaterorEqual([1,2,3,4],3));   // 
console.log(shortestSubarray_GreaterorEqual([1,4,1],5)); // 