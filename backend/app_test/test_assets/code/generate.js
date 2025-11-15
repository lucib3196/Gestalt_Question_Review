

function generate() {
  const a = 1;
  const b = 2;
  const sum = a + b;

  console.log("This is the value of a", a);
  console.log("This is the value of b", b);
  data = { params: { a: a, b: b } };
  console.log("Here is a structure", data);

  return {
    params: { a: a, b: b },
    correct_answers: { sum: sum },
    intermediate: { step: `${a} + ${b} = ${sum}` },
    test_results: { pass: 1, message: "Addition successful" },
    nDigits: 3,
    sigfigs: 3,
  };
}
