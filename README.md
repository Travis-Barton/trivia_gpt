# function documentation

## update_answer_score

This function is used to manually update the score of an answer in the database. It is triggered by an HTTP request and takes one parameter: `request`.

### Parameters:

- `request`: An object that contains data about the HTTP request that triggered the function. This data is expected to be a JSON object with two properties: `user_id` and `answer_id`.

### Functionality:

The function first extracts the `user_id` and `answer_id` from the `request` object. It then loads the answer from the database using the `answer_id`. If the answer is not found, it returns a message indicating this.

If the answer is found, the function updates the `correct` property of the answer to its opposite value and adds a `reason` property to the answer indicating that it was manually altered by an admin. The updated answer is then saved back to the database.

The function finally returns a message indicating that the answer was updated.

### Deployment:

To deploy this function to Google Cloud Functions, you can use the following command:

```bash
gcloud functions deploy update_answer_score \
    --runtime python310 \
    --entry-point update_answer_score \
    --allow-unauthenticated \
    --timeout 540s \
    --memory 1GB \
    --trigger-http \
    --allow-unauthenticated \
    --ignore-file=.gcloudignore
```

### Usage:

To call this function from JavaScript, you can make an HTTP POST request to the function's URL with a JSON body containing the `user_id` and `answer_id`. Here's an example using the `fetch` API:

```javascript
const url = 'https://REGION-PROJECT_ID.cloudfunctions.net/update_answer_score';
const data = { user_id: 'USER_ID', answer_id: 'ANSWER_ID' };

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => {
  console.error('Error:', error);
});
```

Replace `REGION`, `PROJECT_ID`, `USER_ID`, and `ANSWER_ID` with the actual values.

# DB Schema

![DB Schema](docs/db_relationships.png)


# Active todos

1. Show participant scores in a table (winner gets balloons?)
2. Breakdown participant scores by round for trivia master (via the game model)
3. implement the trivia master simple view
4. add footer for my link
5. add a link provided by the trivia master for tips
6. auto-refresh the page when the trivia master updates the game
7. enable image questions
