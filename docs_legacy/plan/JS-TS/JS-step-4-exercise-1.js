const a = { level1: { level2: { x: 1 } } };
const b = { ...a };
const c = JSON.parse(JSON.stringify(a));

b.level1.level2.x = 100;
console.log(a.level1.level2.x); // 100
console.log(c.level1.level2.x); // 1