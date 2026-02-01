# JS-TS Algorithms · enhancement review checklist

## A Series: Subarrays / Sliding Window

- [ ] A1-shortest-subarray-sum.ts   
      - given: ① "positive integers" 
               ② "contiguous subarray"
               ③ return ... that hits the "target" (such as '===' or '<='...)
  - ① Time: 2025/12/28 11:28
      - link: [A1 revisit-1](./enhancement/revisit-1/revisit-1-A1-shortest-subarray-sum.ts)
  - ② Time: 2026/01/04 11:56 <!--7days 28mins-->
      - origin:  ① sum >= target
      - variant: ① sum = target 
      - issues: ① current right - previous left, which means compute a result before --/++
      - link: [A1 revisit-2](./enhancement/revisit-2/revisit-2-A1-shortest-subarray-sum.ts)
  - ③ Time: 2026/01/10 16:15 <!--6 days 4 hrs 19 mins>
      - origin:  ① - needs: "shortestlength"; 
                   - returns: shortestLength
      - variant: ① - needs: "shortestLength", "Subarray(s)/count(s)" that "hit the target" ; 
                   - returns: "an array" for "all possibilities/counts" 
      - issues: ① shortestLength variable should be Infinity, not 0; Otherwise it answer would be 0!
                  let shortestLength = Infinity;
                  ...
                  shortestLength = Math.min(shortestLenfth, currentLength);  
                ② sum -= nums[left]; // remember to subtract the left from sum
                  left++;
      - link: [A1 revisit-3](./enhancement/revisit-3/revisit-3-A1-shortest-subarray-sum.ts)

- [ ] A1B1-shortest-subarray-length.ts  
  - ① Time: 2025/12/31 14:58
      - link: [A1B1 revisit-1](./enhancement/revisit-1/revisit-1-A1B1-shortest-subarray-length.ts)    
  - ② Time: 2026/01/07 12:56 <!--6days 21hours 58mins-->
      - issues: ① prefixsum is counted from 0 as 0 (not just from nums[0] -> prefixsum[1]):
                  - const prefixsum: number[] = [0]; // n+1
                    ...
                  - for (let i = 0; i < prefixsum.length; i++)
                ② const deque: number[] = [] // contains each prefixsum's index
                ③ why curr <= prefixsum[deque[deque.length - 1]!]!; why can be equal?
                  - the index "back" is smaller than "i", even if their prefixsums are equal
                  - k - i < k < k - back; even when prefixsum[back] = prefixsum[k]
                ④ return answer === Infinity ? 0 : answer
                  - equal to Infinity? if yes, 0; no, answer.
      - link: [A1B1 revisit-2](./enhancement/revisit-2/revisit-2-A1B1-shortest-subarray-length.ts) 
  - ③ Time:  

- [ ] A2-fixed-window-max-average.ts  
  - ① Time: 2026/01/11 13:03 
      - origin:  ① "given length(=== length) return max average"
                   - Math.floor(sum / k) will round down
                   - sum / k will find exact value 
      - variant: ① "given average(<= target) return max length"
                   - while (left <= right && average > target) {...} // in order to avoid demominator 100
     - issues: ① if (currLength === k) {...} vs if (currLength > k)
                 when currLength is longer than length k, it means 5 elements are included now
                 so sum (5 elements) / k (4) => wrong computation                 
      - link: [A2 revisit-1](./enhancement/revisit-1/revisit-1-A2-fixed-window-max-average.ts)      
  - ② Time:  
  - ③ Time:  

## B Series: Subarray Sum

- [ ] B1-subarray-sum-count.ts
      - link: [B1 revisit-2](./enhancement/revisit-2/revisit-2-B1-subarray-sum-count.ts)  
  - ① Time: 2025/12/30 12:17  
  - ② Time: 2026/01/04 11:10 <!--4days 22hrs 53mins-->
      - issue: ① Look up (.get) before any insert (.set) - 0 <= j < i <= n
      - link: [B1 revisit-2](./enhancement/revisit-2/revisit-2-B1-subarray-sum-count.ts)

  - ③ Time:  

- [ ] B2-subarray-max-sum(array).ts  
  - ① Time: 2025/12/31 14:58  
      - link: [B2 revisit-1](./enhancement/revisit-1/revisit-1-B2-subarray-max-sum(array).ts)  
  - ② Time: 2026/01/06 23:42 <!--6 days 8 hrs 26 mins-->
      - origin:   ① any array (or just sum)
      - variant : ① the longest/shortest range (say, [1,2,-1,4,0]) the last 0 is counted;
                  - an extra condition: 
                    ...} else if (curr === best && currLength > bestLength) {... 
                    (or currLength < bestLength)
                  ② all ranges (say, [1,2,-1,4,0])
                  - Also maintain two indices (currStart and i)
                    but we need: 
                    const bestArray: Array<[number,number]> = [[0,1]];
                    ...
                    bestArray.push([currStart, i]);
                    ...
                    return bestArray.map(([l,r]) => nums.slice(l,r+1)) // using method .map() to transfrom indices into numbers
      - link: [B2 revisit-2](./enhancement/revisit-2/revisit-2-B2-subarray-max-sum(array).ts)  
  - ③ Time:  

## C Series: Strings

- [ ] C1-longest-substring-without-repeating.ts  
  - ① Time: 2026/01/03 12:00
      - issues: ① distinction between lastIndex(Map) and seen(Set)
      - link: [C1 revisit-1](./enhancement/revisit-1/revisit-1-C1-longest-substring-without-repeating.ts) 

  - ② Time: 2026/01/08 14:30 <!--5 days 2 hrs 30 mins-->
      - origin: ① For "All" versions: 
                  ① if other longest character subarrays are not included;
                    - if (winLen > maxLen) {...}； // skip the "===" condition
                    ...
                    - return s.slice(bestStart, bestStart + maxLen); // only bestStart needs to be maintained
                  ② if (lastIndex.has(ch)) {...} vs if (lastIndex.get(ch)) {...}
                    - to get.(ch): if key exists but with 0 as its value, there'll be bug (if treats 0 as falsy!)
                  ③ Why "while (seen.has(ch)) {...}" then "seen.add"
                    - Look at if any duplicates as adding new character into "old window"
                    - And if we put "seen.add" beforehand, "while (seen.has(ch)) {...}" will tell it as true forever and always gives it pass  
                      so the loop fails since while loop is used to deduplicate the subarray.
                    - Same as why lastIndex.set(ch, right) should be set after the while loop
                      we need those old positions to decide whether we should shrink the window or not; then set the new one:
                      lastIndex.set(ch, right);
                ② For "Map" version:
                  - left = Math.max(left, prev + 1); // dedicated to computing index left
                    ① left: for case(s) outside the window (maintain the left boundary of a window)
                    ② prev + 1: for case(s) inside the window (shrink the window and move it forward from the left) 
                    e.g., (abbaac) -> ab -> b (duplicate: but take "prev + 1") -> ba (duplicate: but take "left") ...
      - variant:  ① if all valid strings should be returned (or as counts):
                    - ...} else if (winLen === maxLen) {...
                     results.push(s.slice(left, right + 1)) // or counts++
                    } 
      - link: [C1 revisit-2](./enhancement/revisit-2/revisit-2-C1-longest-substring-without-repeating.ts)  
                    
  - ③ Time:  

- [ ] C2-first-unique-char.ts  
  - ① Time: 2025/12/26 23:56 
      - from: ./basic/revisit-2/revisit-2-5-map-first-unique-char.ts

  - ② Time: 2026/01/11 21:19 <!--15 days 21 hrs 23 mins-->
      - origin:  ① "First unique character"
                   - indexMap.set(ch, (indexMap.get(ch) ?? 0) + 1)
                     since "??" takes lower priority than "+"
                     "indexMap.get(ch) ?? 0" should be enclosed by parentheses  
      - variant: ① "Second unique character"
                   - Provide Unique character's index as the answer (×)
                     if (indexMap.get(ch) === 1 && count === 0) count++;
                     if (indexMap.get(ch) === 1 && count === 1) return j;
                     What will happen? -> if character 's' has one occurrence -> count++ -> return its index
                     but this is the first unique character!
                   - Second character's index (√)
                     if (indexMap.get(ch) === 1 && count === 0) {
                      count++;
                     } else if (indexMap.get(ch) === 1 && count === 1) {
                      return j;
                     }
      - link: [C2 revisit-1](./enhancement/revisit-1/revisit-1-C2-first-unique-char.ts)  

  - ③ Time:  

- [ ] C3-valid-palindrome-delete-one.ts  
  - ① Time: 2025/12/26 20:55 
      - from: ./basic/revisit-2/revisit-2-4-string-valid-palindrome.ts
              ./basic/revisit-3/revisit-3-2-string.ts

  - ② Time: 2025/01/12 15:41 
      - origin:  ① "At most one"
                   - you don't have to delete any character
      - variant: ① "Exactly one"
                   - you've got to delete one character, even if the string is a palindrome.
                 ③ "Min deletion to make a panlindrome"
                   - use a two dimensional array with DP
                   ① const dp: number[][] = Array.from({ length: n }, () =>
                      Array<number>(n).fill(0)
                      );
                     - Equivalent:
                       const dp: number[][] = [];
                       for (let i = 0; i < n; i++) {
                       const row = new Array<number>(n).fill(0);
                       dp.push(row)
                       }
                     - Equivalent: 
                       const dp: Array<[number[]]> = ... (same as above)
                   ② for (let len = 2; len <= n; len++) {...}
                     - if len < 2, then dp[0]![n - 1]! will never be returned a meaningful result but 0 as initialized
                   ③ const r = l + len - 1;
                     - without l (const r = len - 1) the transitional logic will break (inconsistent calculations one-by-one)
                     - given that len = r - l + 1, r = l + len - 1; such that
                       each dp[l][r] will have a consistent len(length) at each run.
                   ④ dp[l]![r]! = 1 + Math.min(dp[l]![r - 1]!, dp[l + 1]![r]!) 
                     - why not dp[l - 1][r] and dp[l][r + 1]?
                       they mean left or right end addition, rather than its deletion! 
      - link: [C3 revisit-1](./enhancement/revisit-1/revisit-1-C3-valid-palindrome-delete-one.ts) 

  - ③ Time:  

- [ ] C4-string-compress.ts  
      - from: ./basic/revisit-2/revisit-2-3-string-compress.ts
  - ① Time: 2025/12/26 18:18 
  - ② Time:  
  - ③ Time:  

## D Series: Two Sum

- [ ] D1-two-sum-unsorted.ts
      - given: ① "integers"(negative, positive and 0 included) 
               ② "unsorted subarray"
               ③ "return ... that hits the "target" (such as "sum") " 
  - ① Time: 2026/01/01 12:07
      - link: [D1 revisit-1](./enhancement/revisit-1/revisit-1-D1-two-sum-unsorted.ts) 
  - ② Time: 2026/01/10 19:38 <!--9 days, 7 hrs & 31 mins apart-->
      - origin:  
        ① return "any subarray"
        ② sum = target
      - variant: ① simple
                   ① return "counts / all subarrays"
                   ...
                 ② more complex
                   ① return all "counts / subarrays" 
                   ② sum >= target
                   - unnecessary to set another array for number(s) scaned
                     ...
                     for (let i = 0; i < nums.length; i++) {
                      for (let j = 0; j < i; j++) {...}
                     }
                     
                   
      - link: [D2 revisit-2](./enhancement/revisit-2/revisit-2-D1-two-sum-unsorted.ts)   
  - ③ Time:  

- [ ] D2-two-sum-sorted-two-pointers.ts  
      - from: ./basic/revisit-2/revisit-2-7-sum-sorted-two-pointers.ts
  - ① Time: 2025/12/27 17:01 
  - ② Time:  
  - ③ Time:  

## E Series: Frequency / Deduplication / Majority

- [ ] E1-majority-element.ts  
      - given: ① "subarray"
               ② "counting"
  - ① Time: 2025/12/29 19:04
      - link: [E1 revisit-1](./enhancement/revisit-1/revisit-1-E1-majority-element.ts) 
      - origin:  ① classic Map
      - variant: ② Boyer Moore (prerequisite: n > 2)

  - ② Time: 2026/01/05 12:07 <!--6 days 17 hrs 3 mins-->
      - origin:  ① n > 2 (with just one element)
      - variant: ① n > 3, for example (with at least one element)
      - issues: ① to tell whether an array has one element: 
                  - results.include(num)
                  - !results.include(num)
      - link: [E1 revisit-2](./enhancement/revisit-2/revisit-2-E1-majority-element.ts)
  - ③ Time:  

- [ ] E2-unique-single-number.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

- [ ] E3-array-unique-using-set.ts  
      - from: ./basic/revisit-2/revisit-2-6-set-unique.ts
  - ① Time: 2025/12/27 13:20 
  - ② Time:  
  - ③ Time:  

## F Series: Binary Trees

- [ ] F1-tree-sum-of-left-leaves.ts  
  - ① Time: 2025/12/28 14:06  
  - ② Time: 2026/01/05 12:56 <!--7 days 22 hrs 50 mins-->
      - issues: ① Recursive DFS: calls go from top to botoom, returns go from bottom to top
                ② Iterative DFS (stack): visit order is similar to recursive preorder, also from top to bottom (LIFO)
                ③ BFS (queue): visit level by level from top to bottom; no "bottom to top" phase. (FIFO)
      - link: [F1 revisit-2](./enhancement/revisit-2/revisit-2-F1-tree-sum-of-left-leaves.ts)  
  - ③ Time:  

- [ ] F2-binary-tree-level-order.ts  
  - ① Time: 2026/01/06 20:28
      - issues: ① Breadth‑First Search (BFS) with 'queue' (FIFO) 
                  From left to right: (the order below should not be changed)
                  - if (node.left !== null) queue.push(node.left)
                  - if (node.right !== null) queue.push(node.right)
                ② Depth-First Search (DFS) (LIFO)
                  From right to left:
                  - if (node.right) stack.push({node: node.right, level: level + 1})
                  - if (node.left) stack.push({node: node.left, level: level + 1})
                ③ Recursive DFS: 
                  - result[level] = [] means (if level = 0) [  []  ]
                  - if (node === null) return means ends the function immediately without executing the following code
      - link: [F2 revisit-1](./enhancement/revisit-1/revisit-1-F2-binary-tree-level-order.ts) 
  - ② Time:  
  - ③ Time:  

- [ ] F3-binary-tree-max-depth.ts  
      - from: ./basic/revisit-2/revist-2-8-tree-node-max-depth.ts
  - ① Time: 2025/12/27 18:30 
  - ② Time:  
  - ③ Time:  

## G Series: Stack / Queue

- [ ] G1-valid-parentheses.ts  
  - ① Time: 2026/01/04 13:46 
      - issues: ① generic Record<k, T> vs Map<k, v>
                  - two versions: 
                    1. const map: Record<string, string> = {
                      '{': '}',
                      '(': ')',
                      '[': ']',
                    }
                    ...
                    2. if (ch in map) {
                      stack.push(map[ch]!)
                    };
                    - Equivalent: 
                      1. const map = new Map<string, string>([
                        ['{', '}'],
                        ['(', ')'],
                        ['[', ']'],
                      ])
                      ...
                      2. if (map.has(ch)) {
                        stack.push(map.get(ch)!)};
                ② Boolean rules: return stack.length === 0 → true 
      - link: [G1 revisit-1](./enhancement/revisit-1/revisit-1-G1-valid-parentheses.ts)  
  - ② Time: 2026/01/07 20:38 <!--3 days 6 hrs 52 mins-->
      - link: [G1 revisit-2](./enhancement/revisit-2/revisit-2-G1-valid-parentheses.ts)   
  - ③ Time:  

- [ ] G2-min-stack.ts  
  - ① Time: 2026/01/13 19:52
      - issues: ① see an example below about how to use private and .this
                  ...
                  private seen = new Set<number>();
                  private map = new Map<number,number>();
                  ...
                  this.seen.add(x);
                ② v = this.stack.pop()!, probably v > min or v === min (instead of v < min)
                  - since minStack stores an array in descending/decreasing order [5,3], never as [5,3,4]
                ③ to distinguish an empty stack:
                  ① if (this.stack.length) {...}
                  ② if (!this.stack.length) {...}
                  ③ if (this.stack.length !== 0) {...}
                  ④ if (this.stack.length === 0) {...}
                    - when length is certainly a number: ① === ③, ② === ④;
                ④ Operations:
                  ① need an empty-check: pop (return;) / top (undefined) / getMin (undefined) (they read or remove elements)
                    - undefined is a more coherent type, rather than number[] (which you still need to distinguish it from number or string or etc...)
                  ② don't need an empty-check:  push (it only inserts elements)
                    - but about: if (!this.minStack.length || x <= this.minStack[this.minStack.length - 1]!) {...}
                      without "!this.minStack.length ||", length will be calculated to -1 => undefined!
                  ③ if (!stack.length) return;  // <<<- this is the first guard for normal stack
                    ...                        
                    if (minStack.length && minStack[minStack.length - 1]!) {...}  // <<<- this is the second for min stack!
                    theoretically, the second guard won't happen before any modification in the future. Consider it as a defensive programming
                    in case of extra addition and avoiding -1 for later use.
      - link: [G2 revisit-1](./enhancement/revisit-1/revisit-1-G2-min-stack.ts)  

  - ② Time:  

  - ③ Time:  

- [ ] G3-queue-using-stacks.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

## H Series: Linked Lists

- [ ] H1-reverse-linked-list.ts  
  - ① Time: 2026/01/05 15:52 
      - issues: ① Iterative Reassembling of ListNode
                ② We need queue/stack.push() if using queue/stack = [head];
      - link: [H1 revisit-1](./enhancement/revisit-1/revisit-1-H1-reverse-linked-list.ts)  
  - ② Time: 2026/01/09 10:24 <!--3 days 18 hrs 32 mins-->
      - issues: ① why return prev instead of curr.next
                  - each run will move the curr forward to next node (change the reference to which node) until the final one:
                    null. So curr === null; prev is right answer to the question.
      - link: [H1 revisit-2](./enhancement/revisit-2/revisit-2-H1-reverse-linked-list.ts)     
  - ③ Time:  

- [ ] H2-merge-two-sorted-lists.ts  
  - ① Time: 2026/01/08 21:20
      - issues: ① curr.next = p1 => means change to which the list points
                ② p1 = p1.next => means move the list forward to next node
      - link: [H2 revisit-1](./enhancement/revisit-1/revisit-1-H2-merge-two-sorted-lists.ts)    
  - ② Time:   
  - ③ Time: 

- [ ] H3-linked-list-cycle.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

## I Series: Binary Search

- [ ] I1-binary-search-basic.ts  
  - ① Time: 2026/01/06 17:51
      - given: ① "an ascending array"
      - origin:  ① tie-break: only one result
      - variant: ② no tie-break: multi results
      - issues (origin):  ① Computation for index (not "length", so it's unnecessary to + 1): 
                            - const middle = Math.floor((left + right) / 2); 
                          ② We need queue/stack.push() if using queue/stack = [head];
      - issues (variant): ① if (first === -1) return []  
                            - last === -1 condition is ignored, since if first is none, so is last.
                          ② Note: 
                            - solution is to find rightmost / leftmost boundary
                          ③ right/left boundary (to find extreme values / indices)
                          if (val >= mid) { // means val is too large for target -> shrink it to the left
                          ... val = mid
                          right = mid - 1;
                          } // and vice versa       
                          ④ for (let i = first; i <= last; i++) 
                            - that means it starts from a certain number, instead of 0!
                            - so i <= last!
      - link: [I1 revisit-1](./enhancement/revisit-1/revisit-1-I1-binary-search-basic.ts)

  - ② Time: 2026/01/13 15:45 <!--6 days 21 hrs 55 mins-->
      - issues: ① Due to ascending array, 
                  index: left ... <= half .... < right, so 
                  value: nums[mid] ... <= half ... < right
                  so each narrow-down would remove another incorrect half 
                  (maybe left, maybe right, depends on condition "if num[mid] < or > target")
                  let's say shrink to left (right = half - 1):
                    - (left ... half-1) (half ... right), then (left ... half - 1) remains right answer; 
                    - (half ... right) is 100% beyond the scope 
                    - that's why: right = half - 1, if an expansion happens; left = half + 1, if a shrink is possible
      - variant: ① if <= / < / > / >= target, what we need is exactly one boundary:
                   - > / >= target: if nums[nums.length - 1] > / >= target, nums[nums.length - 1] is leftmost index
                   - < / <= target: if nums[nums.length - 1] < / <= target, nums[nums.length - 1] is rightmost index
      - link: [I1 revisit-2](./enhancement/revisit-2/revisit-2-I1-binary-search-basic.ts)

  - ③ Time:  


- [ ] I2-answer-space-binary-search.ts  
  - ① Time:  


## J Series: DFS / Backtracking

- [ ] J1-subsets-backtracking.ts  
  - ① Time: 2026/01/06 17:19
      - issues:  ① result.push([...path]):
                   no matter how path will be changed, the path in the result remain the same
      - link: [J1 revisit-1](./enhancement/revisit-1/revisit-1-J1-subsets-backtracking.ts)
  - ② Time:  
  - ③ Time:  

- [ ] J1D1-all-sums-unsorted-backtrack.ts 
  - ① Time: 2026/01/11 20:50
      - issues:  ① function backtrack(start: number, target: number): number[][] {
                   for (let i = start; i < nums.length; i++) {...} }
      - link: [J1D1 revisit-1](./enhancement/revisit-1/revisit-1-J1D1-all-sums-unsorted-backtrack.ts)
  - ② Time:  
  - ③ Time:  

- [ ] J2-permutations-backtracking.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

- [ ] J3-islands-count-dfs.ts  
  - ① Time:  
  - ② Time:   
  - ③ Time: 

## K Series: Intervals / Greedy

- [ ] K1-merge-intervals.ts  
  - ① Time: 2026/01/08 17:39
      - issues:  ① Array<[number,number]> = [] vs number[][]  
                   - Array<[number,number]> = dictates a tuple with fixed length of 2
                     - [1,2], [3,4]
                   - number[][] gives a tuple with any length
                     - [1], [1,2], [1,2,3]
                 ② const sort = [...intervals].sort((a,b) => (a[0] - b[0]))
                   - if a: [1,6] b: [2,4] => [[1,6], [2,4]] since the array is sorted by start (index 0)
                   - so if (currEnd >= start) {
                     currEnd = Math.max(currEnd,end);
                     }
                 ③ const [start,end] = sort[i]!;
                   ...
                   ...} else {...
                    currStart = start;
                    currEnd = end;
                   }
      - link: [k1 revisit-1](./enhancement/revisit-1/revisit-1-K1-merge-intervals.ts)    
  - ② Time:  
  - ③ Time:  

- [ ] K2-insert-interval.ts  
  - ① Time: 2026/01/13 12:16
      - given: ① "an ascending array by start of tuples" 
               ② "interval-merging"
      - origin:  ① "insert one interval"
      - variant: ① "merge two interval lists"
                   - compare "push two intervals until either one is finished" with "all pushed together, then sorted"
                       const all = [...a, ...b];
                       all.sort((x,y) => x[0] - y[0]);
                     the former version can be more efficient by making use of the prerequiste: two ascending lists
                   - mergedByStart.push(a[i++]!);
                     Equivalent: 
                       - mergedByStart.push(a[i]!);
                         i++;
                  ② "merge two interval lists" + "comparison of s with res[res.length - 1]![1]"
                    ① const pickNext = (): [number,number] | undefined => {...}
                      which is a function without any argument
                    ② while (true) {
                      const next = pickNext();
                      if (!next) break; // if next === undefined, exit the loop
                      // all lines below before the closing brace belong to "else" 
                      ...
                     }
                    ③ "why block below may go wrong?"
                      ① ...
                        const [nextStart, nextEnd] = next;
                        let resEnd = res[res.length - 1]![1]； // the last interval's end is redirected to resEnd, which is undefined as initial 
                        if (!res.length || resEnd < nextStart) {  //   ↓  res has at least one interval || last interval's end < next interval's start
                            res.push([nextStart, nextEnd]);       //   ↓  case 1: no overlap. Start a new interval
                        } else {                                  //   ↓  case 2: Overlap. Merge them into one, but...
                            resEnd = Math.max(resEnd, nextEnd);   // the real end would've been updated... We updated resEnd instead!     
                        }
                        ...
                      ① correct coding:
                        ...
                        const [nextStart, nextEnd] = next;
                        if (!res.length || res[res.length - 1]![1] < nextStart) {
                          res.push([nextStart, nextEnd]);
                        } else {
                          res[res.length - 1]![1] = Math.max(res[res.length - 1]![1], nextEnd);
                        };
                        ...
                      
                    ④ const [s,e] = next; // array destructuring assignment -> 
                      const s = next[0];
                      const e = next[1];

              
  - ② Time:  
  - ③ Time:  

- [ ] K3-meeting-rooms.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

- [ ] K4-jump-game.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

## L Series: Dynamic Programming

- [ ] L1-climbing-stairs.ts  
  - ① Time: 2026/01/10 14:34
      - issues:  ① For memo version:
                   If n = 5; here's how it is computed: (by order the machine will compute the left one)
                      -                  ↓ memo[5] undefined 
                      - memo(5) = climbStairsMemo(4, memo) + climb(3,memo) // memo[3] is called back here!
                      -                  ↓ memo[4] undefined       ↑ 
                      - memo(4) = climbStairsMemo(3, memo) + 2     ↑    
                      -                  ↓ memo[3] undefined       ↑
                      - memo(4) =        2  +  1 = 3      // memo[3] is stored in cache!       
      - link: [L1 revisit-1](./enhancement/revisit-1/revisit-1-L1-climbing-stairs.ts)      
  - ② Time:  
  - ③ Time:  

- [ ] L2-house-robber.ts  
  - ① Time: 2026/01/12 19:58
      - issues: ① if (n === 0) return 0;        // means nothing; ≠ dp[0]
                  if (n === 1) return nums[0]!; // = dp[0], where '0' is an index
                  ...
                  let prev2 = nums[0]!;                     // dp[i-2] => dp[0]
                  let prev1 = Math.max(nums[0]!, nums[1]!); // dp[i-1] => (say) 9 vs 7 => 9
      - link: [L2 revisit-1](./enhancement/revisit-1/revisit-1-L2-house-robber.ts)    
  - ② Time:  
  - ③ Time:  

- [ ] L3-LIS-basic.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

- [ ] L4-knapsack-01-idea.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

## M Series: Graphs / BFS / DFS

- [ ] M1-number-of-islands.ts  
  - ① Time: 2026/01/10 15:04
      - issues:  ① How dfs flows from this 1 to other 1(s) (and avoid 0) 
                   let's say grid[0][0], here 
                   ① "√ / x" means successfully filled in or not (if nothing happens, area is left blank)
                   ② and ".No" here means which turn it fills in with "0"
                   - 1(√1)  -  1(√1)  - 0(x2) -
                   - 1(√1)  -  1(√2)  - 0(x2) -
                   - 0(x2)  -  0(x2)  - 0(  ) -
                ① : void {...} means the function returns no value
                ③ let rows = grid.length  ...  r >= rows means the index r should be "no more than length - 1"
                    - once r === rows, it has already crossed the boundary
      - link: [M1 revisit-1](./enhancement/revisit-1/revisit-1-M1-number-of-islands.ts) 

  - ② Time:  

  - ③ Time:  

- [ ] M2-shortest-path-grid-bfs.ts  
  - ① Time: 
      - issues: ① const dirs: [number,number][] = [...] equivalent to:
                  const dirs: Array<[number,number]> = [...]
                  ...
                ② initialize visited:
                  ① -> Good version:
                    const visited: boolean[][] = Array.from({ length: rows}, () =>
                    Array(cols).fill(false));
                    ⭐ Each line is a new array (independen of each other)
                  ② -> Bad version
                    const visitedBad = new Array(rows).fill(new Array(cols).fill(false));
                    ⭐ Just one change will lead to changes of all lines、
                  ③ why for "fromUp" it's unnecessary to add "r > 0 ？ ... : 0"
                    - since const dp = new Array<number>(cols).fill(0), then first row (0) is initialized as 0
                    - Assume that there are no blocks, for (0,0...n) = 1, dp[0...n] = 0(fromUp) + 1(fromLeft) = 1;
                  ④ const fromUp = dp[c]!;
                    - from same index (r) so dp[c] comes from old value one step above.  
      - link: [M2 revisit-1](./enhancement/revisit-1/revisit-1-M2-shortest-path-grid-bfs.ts)  

  - ② Time:  
  
  - ③ Time:  

- [ ] M3-open-lock-bfs.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time:  

- [ ] M4-graph-bfs-template.ts  
  - ① Time:  
  - ② Time:  
  - ③ Time: