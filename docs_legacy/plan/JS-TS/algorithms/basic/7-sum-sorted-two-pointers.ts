// 题 7：有序数组的两数之和（Two Pointers）
// 给定一个升序排列的整数数组 nums 和一个目标值 target，
// 找出和为 target 的两个数的下标（假设一定存在且唯一）。

// - 输入：nums = [1,2,4,6,10], target = 8 → 输出 [1,3]（2 + 6）。
// - 要求：
// 1) 时间复杂度 O(n)；
// 2) 不使用额外数组复制。

function twoSumSorted(numbers: number[], target: number): [number, number] | null {
    let left = 0;
    let right = numbers.length - 1;

    while (left < right) {
        const sum = numbers[left]! + numbers[right]!;

        if (sum === target) {
            return [left, right];
        } else if (sum < target) {
            left ++;
        } else { // sum > target
            right --;
        }
        }
    return null;
}


// 简单自测
console.log(twoSumSorted([1, 2, 4, 6, 10], 8)); // [1, 3] -> 2 + 6