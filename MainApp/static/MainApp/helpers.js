
export function sendFriendData(url, data) {
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); // Log the response data
        if(data && data.message) {
            console.log('data.message');
        } else {
            console.log('Problem');
        }
    })
    .catch(error => {
        console.log('Error:', error);
    });
}

export function generateThankYouPage(appendTo, placeholder, url) {
    appendTo.innerHTML = ''
    let thankYouContainer = document.createElement('div')
    let thankYouTitle = document.createElement('h2')
    thankYouTitle.textContent = 'Thank You!'
    let thankYouSubTitle = document.createElement('h5')
    thankYouSubTitle.textContent = `Your ${placeholder} has been created`

    if(url !== '#') {
        let backButton = document.createElement('button')
        let backButtonLink = document.createElement('a')
        backButtonLink.href = url
        backButtonLink.textContent = `Back to all ${placeholder}s`
        backButton.appendChild(backButtonLink)
        thankYouContainer.appendChild(backButton)
    }

    thankYouContainer.appendChild(thankYouTitle)
    thankYouContainer.appendChild(thankYouSubTitle)
    appendTo.appendChild(thankYouContainer)
}

export function sendData(url, data, appendTo, placeholder, link, errorMessage) {
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); // Log the response data
        if(data && data.message == "Successfully added") {
            console.log('data.message');
            generateThankYouPage(appendTo, placeholder, link)
        } else if(data && data.message != "Successfully added" ) {
            errorMessage.textContent = data.message
        }else {
            console.log('Problem');
        }
    })
    .catch(error => {
        console.log('Error:', error);
    });
}