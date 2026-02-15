function leftBoundaryGreater(nums: number[], target: number) {
    let left = 0;
    let right = nums.length - 1;
    // since no index has a number less than 0 
    let first = -1;

    while (left <= right) {
        const half = Math.floor((left + right) / 2);
        if (nums[half]! > target) {
            first = half;
            right = half - 1; // move left
        } else {
            left = half + 1;
        }
    }
    return first;
}


function extractAllIndicesGreater(nums: number[], target: number): number[] {
    const first = leftBoundaryGreater(nums, target);
    if (first === -1) return [];

    const res: number[] = [];
    for (let i = first; i <= nums.length; i++) {
        res.push(i);
    }
    return res;
}

console.log(extractAllIndicesGreater([1,3,5,7,9,9,9],6));
console.log(extractAllIndicesGreater([],0));
console.log(extractAllIndicesGreater([0,3,5,7,9,9],0));