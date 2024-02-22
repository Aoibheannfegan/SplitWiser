import { sendData, generateThankYouPage } from './helpers.js'

document.addEventListener('DOMContentLoaded', () => {
    let settleUpBtn = document.getElementById('settleUp')
    if(settleUpBtn != null) {
        settleUpBtn.addEventListener('click', makePayment)
    }
})

function makePayment() {
    console.log('Settle Up Button clicked')

    let oustandingBalanceStatus = document.querySelector('.group-amount')

    let userElement = document.getElementById('userTitle')
    let friendElement = document.getElementById('friendTitle')
    let user = userElement.getAttribute('name');
    let friend = friendElement.getAttribute('name');

    console.log(`user is ${user} and friend is ${friend}`)

    let settleUpBtn = document.getElementById('settleUp')
    let makePaymentForm = document.getElementById('makePaymentForm')
    makePaymentForm.innerHTML = ''
    let paymentMessage = document.createElement('label')
    paymentMessage.textContent = 'You are paying'
    let paymentInput = document.createElement('input')
    let amountOwed = Math.abs(settleUpBtn.name)
    paymentInput.value = amountOwed
    paymentInput.readOnly = true
    let submitBtn = document.createElement('button')
    submitBtn.textContent = 'Mark as Paid'

    let paymentData = {
        user: user,
        friend: friend,
        amount: amountOwed,
    }

    submitBtn.addEventListener('click', (e) => {
        e.preventDefault()
        sendData('add_payment', paymentData, makePaymentForm, 'payment', '#', 'errorMessage')
        oustandingBalanceStatus.textContent = ''
        oustandingBalanceStatus.textContent = 'No Outstanding Balance'
        userElement.textContent = ''
        friendElement.textContent = ''
        settleUpBtn.style.display = 'none'
    })

    makePaymentForm.appendChild(paymentMessage)
    makePaymentForm.appendChild(paymentInput)
    makePaymentForm.appendChild(submitBtn)
}

