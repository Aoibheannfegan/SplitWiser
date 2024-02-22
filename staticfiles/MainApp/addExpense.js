import { sendData } from './helpers.js'

document.addEventListener('DOMContentLoaded', () => {

    let expensePage = document.getElementById('add-expense-section-container')

    if(expensePage !== null) {
        // get elements
        let groupBtn = document.getElementById('groupBtn')
        let groupOptions = document.getElementById('select-expense-group')

        let memberBtn = document.getElementById('memberBtn')
        let memberOptions = document.getElementById('select-expense-members')

        let formPartOne = document.getElementById('addExpenseFormPartOne')
        let formPartTwo = document.getElementById('addExpenseFormPartTwo')
        let formPartThree = document.getElementById('addExpenseFormPartThree')
        formPartTwo.style.display = 'none'
        formPartThree.style.display = 'none'

        let formPartOneSubmit = document.getElementById('submitFormPartOne')
        let goBack = document.getElementById('backBtn')
        let descriptionElement = document.getElementById('descriptionElement')
        let amountElement = document.getElementById('inputAmount')
        let splitOptionsBtn = document.getElementById('splitOptionsBtn')
        let errorMessage = document.getElementById('errorMessage')

        let finalSubmissionBtn = document.getElementById('submitFormBtn')

        //track which friends and groups have been selected
        let friendsSelection = []
        let uniqueFriendsSelection = []
        let groupSelection = []


        //display groups or friends depending on option selected
        groupBtn.addEventListener('click', (e) => {
            e.preventDefault()
            groupOptions.style.display =  'block'
            memberOptions.style.display = 'none'
            groupBtn.style.backgroundColor = '#20c997'
            groupBtn.style.color = 'white';
            memberBtn.style.backgroundColor = '#F1F1F1'
            memberBtn.style.color = '#20c997'
        })

        memberBtn.addEventListener('click', (e) => {
            e.preventDefault()
            groupOptions.style.display =  'none'
            memberOptions.style.display = 'block'
            groupBtn.style.backgroundColor = '#F1F1F1'
            groupBtn.style.color = '#20c997';
            memberBtn.style.backgroundColor = '#20c997'
            memberBtn.style.color = 'white'
        })

        //handle user clicking on 'Next Step' button
        formPartOneSubmit.addEventListener('click', async (e) => {
            e.preventDefault()
            
            //clear any existing settings/ messages and friends array
            errorMessage.textContent=''
            amountElement.readOnly = false
            descriptionElement.readOnly = false
            amountElement.style.backgroundColor = 'white'
            descriptionElement.style.backgroundColor = 'white'
            

            friendsSelection.splice(0, friendsSelection.length)
            groupSelection.length = 0
            let selectedFriendsListElement = document.getElementById('friendsAddedList')
            selectedFriendsListElement.innerHTML = ''

            //hide part 1 of form and display part 2
            formPartOne.style.display = 'none'
            formPartTwo.style.display = 'block'
            finalSubmissionBtn.style.display = 'block'

            //check which friends have been clicked and add them to friends selection arry
            let selectedFriends = document.querySelectorAll('.friends-checked')
            selectedFriends.forEach(friend => {
                if(friend.checked) {
                    friendsSelection.push(friend.value)
                } 
            })

            //check which groups have been selected, query the db for the members of the selected group and add members to friendsSelection array
            let selectedGroup = document.querySelectorAll('.group-checked')
            selectedGroup.forEach(group => {
                if(group.checked) {
                    groupSelection.push(group.value)
                }
            })
            if (groupSelection.length > 0) {
                // friendsSelection.length = 0
                try {
                    const response = await fetch('/get_dashboard_data');
                    const data = await response.json();
                    const userGroups = data.user_groups.data;
        
                    groupSelection.forEach(group => {
                        const groupData = userGroups.find(item => item[group]);
                        if (groupData) {
                            friendsSelection.push(...groupData[group]);
                        }
                    });

                } catch (error) {
                    console.error('Error fetching group members:', error);
                }
            }
            //remove duplicates from selection
            uniqueFriendsSelection = Array.from(new Set(friendsSelection));

            //display a list of selected friends with duplicates removed
            uniqueFriendsSelection.forEach(friend => {
                let friendListItem = document.createElement('li');
                friendListItem.textContent = friend;
                friendListItem.className = "friendsAddedListItem";
                selectedFriendsListElement.appendChild(friendListItem);
            });
            console.log(friendsSelection);

        })

        splitOptionsBtn.addEventListener('click', (e) => {
            e.preventDefault()
            let description = descriptionElement.value
            let amount = amountElement.value
            
            //check applicable fields are filled in before proceeding
            if(description == "") {
                errorMessage.textContent = 'Please add a description'
            } else if(amount == "") {
                errorMessage.textContent = 'Please add an amount'
            } else {
                //make inputs read only so values can no longer be edited
                errorMessage.textContent = ''
                amountElement.readOnly = true
                amountElement.style.backgroundColor = '#F1F1F1'
                descriptionElement.readOnly = true
                descriptionElement.style.backgroundColor = '#F1F1F1'

                splitOptionsBtn.style.color = "white"
                splitOptionsBtn.style.backgroundColor = "#20c997"

                formPartOne.style.display = 'none'
                formPartTwo.style.display = 'block'
                formPartThree.style.display = 'block'

                let evenBtn = document.getElementById('evenBtn')
                let unevenBtn = document.getElementById('unevenBtn')
                let percentBtn = document.getElementById('percentBtn')

                renderEvenSplitForm(uniqueFriendsSelection)

                evenBtn.addEventListener('click', () => renderEvenSplitForm(uniqueFriendsSelection))
                unevenBtn.addEventListener('click', () => renderUnevenSplitForm(uniqueFriendsSelection))
                percentBtn.addEventListener('click', () => renderPercentForm(uniqueFriendsSelection))    
            }
        })

        finalSubmissionBtn.addEventListener('click', e => handleSubmit(e))

        goBack.addEventListener('click', (e) => {
            e.preventDefault()
            friendsSelection.length = 0
            groupSelection.length = 0
            formPartOne.style.display = 'block'
            formPartTwo.style.display = 'none'
            formPartThree.style.display = 'none'
            finalSubmissionBtn.style.display = 'none'
        })
    }
    
})

function renderEvenSplitForm(friends) {
    let splitFormElement = document.getElementById('splitForm')
    let splitOptionsBtn = document.getElementById('splitOptionsBtn')
    splitOptionsBtn.textContent = 'Evenly'
    splitFormElement.innerHTML = ''
    friends.forEach((friend) => {
        let formContainer = document.createElement('div')
        formContainer.className = "form-check"

        let formInput = document.createElement('input')
        formInput.type = 'checkbox'
        formInput.checked = true
        formInput.value = 'friend'
        formInput.className = "form-check-input friends-checked"
        formInput.id = 'defaultCheck1'

        let formLabel = document.createElement('label')
        formLabel.for = "defaultCheck1"
        formLabel.className ="form-check-label"
        formLabel.textContent = friend
        
        formContainer.appendChild(formInput)
        formContainer.appendChild(formLabel)
        splitFormElement.appendChild(formContainer)
    })
}

function renderUnevenSplitForm(friends) {
    let splitFormElement = document.getElementById('splitForm')
    let splitOptionsBtn = document.getElementById('splitOptionsBtn')
    splitOptionsBtn.textContent = 'Unevenly'
    splitFormElement.innerHTML = ''
    friends.forEach((friend) => {
        let formContainer = document.createElement('div')
        formContainer.className = 'form-line'
        let formLabel = document.createElement('label')
        formLabel.textContent = friend
        let formInput = document.createElement('input')
        formInput.type = 'number'
        formInput.step = '0.01'
        formInput.placeholder = "$0.00"
        formInput.name = friend.replace(/\s/g, '')
        formInput.addEventListener('change', calculateExpenseRemaining)
        formContainer.appendChild(formLabel)
        formContainer.appendChild(formInput)
        splitFormElement.appendChild(formContainer)
    })
}

function renderPercentForm(friends) {
    let splitFormElement = document.getElementById('splitForm')
    let splitOptionsBtn = document.getElementById('splitOptionsBtn')
    splitOptionsBtn.textContent = 'By Percentage'
    splitFormElement.innerHTML = ''
    friends.forEach((friend) => {
        let formContainer = document.createElement('div')
        formContainer.className = 'form-line'
        let formLabel = document.createElement('label')
        formLabel.textContent = friend
        let formInput = document.createElement('input')
        formInput.type = 'number'
        formInput.placeholder = "0%"
        formInput.addEventListener('change', calculateExpenseRemaining)
        formContainer.appendChild(formLabel)
        formContainer.appendChild(formInput)
        splitFormElement.appendChild(formContainer)
    })
}

function calculateExpenseRemaining() {
    console.log('calculate expense function running')
    let splitOptionsBtn = document.getElementById('splitOptionsBtn')
    let expenseRemainingMessage = document.getElementById('expenseRemainingMessage')

    expenseRemainingMessage.textContent = ''

    let formContainers = document.querySelectorAll('#splitForm div');
    let amount = document.getElementById('inputAmount').value
    let sum = 0
    let expenseRemaining = 0

    if (splitOptionsBtn.textContent == 'Unevenly') {
        console.log('calculating expense remaining on uneven form')
        formContainers.forEach((container) => {
            let inputValue = container.querySelector('input').value;
            if(inputValue.trim() !== '') {
                sum += parseFloat(inputValue);
            }
        })
        expenseRemaining = parseFloat(amount) - sum
        parseFloat(expenseRemaining) == 0 ? expenseRemainingMessage.textContent = 'All paid!':expenseRemainingMessage.textContent = `$${sum.toFixed(2)} paid. $${expenseRemaining.toFixed(2)} to go.`
    
    } else if(splitOptionsBtn.textContent == 'By Percentage') {
        formContainers.forEach((container) => {
            let inputValue = container.querySelector('input').value;
            if(inputValue.trim() !== '') {
                sum += parseFloat(inputValue);
            }
        })
        expenseRemaining = 100 - sum
        parseFloat(expenseRemaining) == 0 ? expenseRemainingMessage.textContent = 'All paid!':expenseRemainingMessage.textContent = `${sum}% paid. ${expenseRemaining}% to go.`
    } else {
        expenseRemainingMessage.textContent = ''
    }
    
}

function handleSubmit(e) {
    e.preventDefault()
    let groupChoice = ''
    let selectedGroup = document.querySelectorAll('.group-checked')
    selectedGroup.forEach(group => {
        if(group.checked) {
            groupChoice = group.value
        }
    })
               
    let addExpenseContainer = document.getElementById('add-expense-section-container')
    let errorMessage = document.getElementById('addExpenseErrorMessage')
    let splitOptionsBtn = document.getElementById('splitOptionsBtn')
    let amount = parseFloat(document.getElementById('inputAmount').value)
    let description = document.getElementById('descriptionElement').value
    console.log(amount)
    let formContainers = document.querySelectorAll('#splitForm div');
    let formData = {
        expenseInputs: {
            amount: amount,
            description: description,
        },
        group: groupChoice,
        userInputs: {},
    }

    if (splitOptionsBtn.textContent == 'Unevenly') {
        formContainers.forEach((container) => {
            let labelText = container.querySelector('label').textContent;
            let inputValue = container.querySelector('input').value;
    
            if(inputValue.trim() !== '') {
                formData.userInputs[labelText] = parseFloat(inputValue);
            }
        })
    } else if(splitOptionsBtn.textContent == 'By Percentage') {
        formContainers.forEach((container) => {
            let labelText = container.querySelector('label').textContent;
            let inputValue = container.querySelector('input').value;
            if(inputValue.trim() !== '') {
                formData.userInputs[labelText] = (parseFloat(amount) * (parseFloat(inputValue) / 100)).toFixed(2);
            }
        })
    } else {
        let checkedFriendscount = 0
        formContainers.forEach(container => {
            let formInput = container.querySelector('input')
            if(formInput.checked) {
                checkedFriendscount += 1
            }
        })
        console.log(checkedFriendscount)
        formContainers.forEach((container) => {
            let formInput = container.querySelector('input')
            let labelText = container.querySelector('label').textContent;
            if(formInput.checked) {
                formData.userInputs[labelText] = (parseFloat(amount) / checkedFriendscount).toFixed(2);
            }
        })
    }
    
    sendData('/add_expense', formData, addExpenseContainer, 'expense', "expenses", errorMessage)
}
