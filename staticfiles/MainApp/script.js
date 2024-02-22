import { sendData, generateThankYouPage } from './helpers.js'

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded')

    const makePaymentForm = document.getElementById('make-payment-form')
    if(makePaymentForm != null) makePaymentForm.addEventListener('change', checkRemainingBalance)
    
    const selectGroup = document.getElementById('choose-group')
    if(selectGroup != null) selectGroup.addEventListener('change', handleExpenseForm)
    
    const selectSplitOption = document.getElementById('split-options')
    if(selectSplitOption != null) selectSplitOption.addEventListener('change', handleExpenseForm)
    
    const addAmount = document.getElementById('expense-amount-input')
    if (addAmount != null) addAmount.addEventListener('change', handleExpenseForm)

    const addGroupButton = document.getElementById('addGroupButton')
    if(addGroupButton != null) addGroupButton.addEventListener('click', e => {
        e.preventDefault()
        let addGroupContainer = document.getElementById('addGroupContainer')
        let errorMessage = document.getElementById('addGroupErrorMessage')
        let groupName = document.getElementById('newGroupTitle').value
        let selectedFriends = document.querySelectorAll('.friends-checked')
        let checkedFriendsCount = 0
        
        if(groupName == '') {
            errorMessage.textContent = 'Please add a group name'
            return 
        }
        const groupFormData = {
            group_name: groupName,
            members: {}
        }
        selectedFriends.forEach(friend => {
            if(friend.checked) {
                checkedFriendsCount += 1
                groupFormData.members[friend.name] = (friend.value)
            } 
        })
        if(checkedFriendsCount == 0) {
            errorMessage.textContent = 'Please select at least one group member'
            return 
        }
        sendData('/add_group', groupFormData, addGroupContainer, 'group', "groups", errorMessage)
    })

    const addFriendButton = document.getElementById('addFriendButton')
    console.log(addFriendButton)
    if(addFriendButton != null) addFriendButton.addEventListener('click', e => {
        e.preventDefault()
        console.log('addFriendButton clicked')
        let friendContainer = document.getElementById('addFriendContainer')
        let errorMessage = document.getElementById('addFriendErrorMessage')
        let message=document.getElementById('addFriendErrorMessage')
        message.textContent = ''
        let emailElement = document.getElementById('friendEmail')
        let email = emailElement.value
        if(email == '') {
            message.textContent = 'Please add an email'
        }
        else {
            let addFriendData = {email: email}
            sendData('/add_friend', addFriendData, friendContainer, 'friend', "add_friend", errorMessage)
        }
    })
})


function handleExpenseForm() {
    const selectGroup = document.getElementById('choose-group')
    let groupId = selectGroup.value

    const selectSplit = document.getElementById('split-options')
    let splitType = selectSplit.value

    let amountElement = document.getElementById('expense-amount-input')
    let amount = amountElement.value

    fetch('/get_group_members/' + groupId)
        .then(response => response.json())
        .then(data => {
            //generate a list of members with an input for how much each member owes
            var select = document.getElementById('choose-members');
            select.innerHTML = '';

            var splitList = document.getElementById('split-expense');
            splitList.innerHTML = '';

            let membersCount = data.members.length
            let dollarAmount = amount/membersCount
            let percentageAmount = (100/membersCount).toFixed(2)
            console.log(`$:${dollarAmount} %:${percentageAmount}`)
        
            data.members.forEach(member => {
                var option = document.createElement('option');
                option.value = member.id;
                option.textContent = member.username;
                option.selected = true;
                select.appendChild(option);

                var listItem = document.createElement('li');
                var listItemInput = document.createElement('input');
                listItemInput.type = 'number'
                if(splitType === 'percentage' || splitType === 'dollar') {
                    listItemInput.value = ''
                } else {
                    listItemInput.value = dollarAmount
                }

                listItem.appendChild(listItemInput);
                splitList.appendChild(listItem);
            })
            console.log(splitList)
            
        })
}


function checkRemainingBalance() {
    let remainingBalance = parseFloat(document.getElementById('balance-remaining').textContent)
    
    let amountPaid = parseFloat(document.getElementById('make-payment-amount').value)
    let balance = remainingBalance - amountPaid
    console.log(balance)

    let amountToGoElement = document.getElementById('balance-message')
    amountToGoElement.textContent=''

    if(balance < 0) {
        amountToGoElement.textContent = `You're paying $${Math.abs(balance).toFixed(2)} too much. You owe ${remainingBalance}.`
    } else if(balance > 0) {
      amountToGoElement.textContent = `$${balance.toFixed(2)} remaining to pay bill.`
    }
}

