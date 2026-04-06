var store = require('app-store-scraper');

store.reviews({
  id: '1567841142',
  sort: store.sort.RECENT,
  page: 1
}).then(reviews => {
  console.log(`Found ${reviews.length} reviews on page 1`);
}).catch(console.log);

