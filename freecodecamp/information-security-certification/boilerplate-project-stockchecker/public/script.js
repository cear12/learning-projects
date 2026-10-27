document.getElementById('testForm2').addEventListener('submit', e => {
  e.preventDefault();
  const stock = e.target[0].value;
  const checkbox = e.target[1].checked;
  fetch('/api/stock-prices/?stock=' + encodeURIComponent(stock) + '&like=' + checkbox)
    .then(res => res.json())
    .then(data => {
      document.getElementById('jsonResult').innerText = JSON.stringify(data);
    });
});

document.getElementById('testForm').addEventListener('submit', e => {
  e.preventDefault();
  const stock1 = e.target[0].value;
  const stock2 = e.target[1].value;
  const checkbox = e.target[2].checked;
  const params = new URLSearchParams();
  params.append('stock', stock1);
  params.append('stock', stock2);
  params.set('like', checkbox);
  fetch('/api/stock-prices?' + params.toString())
    .then(res => res.json())
    .then(data => {
      document.getElementById('jsonResult').innerText = JSON.stringify(data);
    });
});
