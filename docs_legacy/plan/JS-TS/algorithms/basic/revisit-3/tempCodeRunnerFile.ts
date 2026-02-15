
function stringCompressPointer(s: string): string {

    if (s.length === 0) return '';

    let count = 1;
    let curr = s[0]!;
    let res: string = ''

    for (let i = 1; i < s.length; i++) {

        const x = s[i]!;
        if (curr === x) {
            count ++;
        } else {
            res += count > 1 ? curr + String(count) : curr;
            count = 1;
            curr = x; 
        }
    }

     res += count > 1 ? curr + String(count) : curr;
     return res; 

}

console.log(stringCompressPointer('Stttring'));
console.log(stringCompressPointer('aaaabbbccca'));