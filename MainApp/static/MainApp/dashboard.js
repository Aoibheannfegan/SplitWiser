// document.addEventListener('DOMContentLoaded', () => {
//     let dashboard = document.getElementById('dashboard')
//     console.log(`Dashboard is ${dashboard}`)

//     if(dashboard != null) {
//         let youOweCanvas = document.getElementById('youOweChart')
//         let friendsOweCanvas = document.getElementById('friendsOweChart')
//         let friendsOwedCanvas = document.getElementById('friendsOwedChart')
//         let groupsOweCanvas = document.getElementById('groupsOweChart')
//         let groupsOwedCanvas = document.getElementById('groupsOwedChart')
//         if(youOweCanvas !== null) {
//             console.log(`You owe Canvas was found`)
//         }

//         let friendFilter = document.getElementById('friendFilter');
//         let groupFilter = document.getElementById('groupFilter');

//         friendFilter.addEventListener('change', updateCharts)
//         groupFilter.addEventListener('change', updateCharts)

//         let youOweChart = getBarChart(youOweCanvas, "Test")
//         let friendsOweChart = getPieChart(friendsOweCanvas, "Test")
//         let friendsOwedChart = getPieChart(friendsOwedCanvas, "Test")
//         let groupsOweChart = getBarChart(groupsOweCanvas, "Test")
//         let groupsOwedChart = getBarChart(groupsOwedCanvas, "Test")

//         loadChart(youOweChart, '/get_dashboard_data', "user_owes" )
//         loadChart(friendsOweChart, '/get_dashboard_data', "friends_owe" )
//         loadChart(friendsOwedChart, '/get_dashboard_data', "friends_owed" )
//         loadChart(groupsOweChart, '/get_dashboard_data', "groups_owe" )
//         loadChart(groupsOwedChart, '/get_dashboard_data', "groups_owed" )


//         function updateCharts() {
//             let friendId = friendFilter.value
//             let groupId = groupFilter.value;
            
//             let url = ''

//             if (friendId !== "" && groupId !=="") {
//                 url=`/get_friends_group_filtered_data/${friendId}/${groupId}`
//             } else if (friendId !== "" && groupId === "") {
//                 url = `/get_friends_filtered_data/${friendId}`;
//             } else if (friendId === "" && groupId !== "") {
//                 url = `/get_group_filtered_data/${groupId}`;
//             } else {
//                 url = `get_dashboard_data`
//             }
//             console.log(`url: ${url}`)

//             loadChart(youOweChart, url, "user_owes" )
//             loadChart(friendsOweChart, url, "friends_owe" )
//             loadChart(friendsOwedChart, url, "friends_owed" )
//             loadChart(groupsOweChart, url, "groups_owe" )
//             loadChart(groupsOwedChart, url, "groups_owed" )
//             console.log(`calls made to get filtered data`)
//             console.log(`YouOweCanvas: ${youOweCanvas}`)
//         }

//         function getBarChart(appendTo, title) {
//             return new Chart(appendTo, {
//                 type: "bar",
//                 options: {
//                     indexAxis: 'y',
//                     animation: false,
//                     legend: {
//                         display: false
//                     },
//                     title: {
//                         display: false,
//                         text: title
//                     },
//                     scales: {
//                         x: {
//                             display: false,
//                             grid: {
//                                 display: false
//                             }
//                         },
//                         y: {
//                             display: true, 
//                             grid: {
//                                 display: false 
//                             }
//                         }
//                     }
//                 }
//             });
//         }

//         function getPieChart(appendTo, title) {
//             return new Chart(appendTo, {
//                 type: "pie",
//                 options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 aspectRatio: 1,
//                 title: {
//                     display: false,
//                     text: title
//                 },
//                 layout: {
//                     padding: {
//                     left: 0,
//                     right: 0,
//                     top: 0,
//                     bottom: 25
//                     }
//                 }
//                 }
//             });
//         }

//         function loadChart(chart, endpoint, chartType) {
//             $.ajax({
//                 url: endpoint,
//                 type: "GET",
//                 dataType: "json",
//                 success: (jsonResponse) => {
//                     const title = jsonResponse[chartType].title;
//                     const labels = jsonResponse[chartType].data.labels;
//                     const datasets = jsonResponse[chartType].data.datasets
                
//                     chart.data.datasets = [];
//                     chart.data.labels = [];


//                     chart.options.title.text = title;
//                     chart.options.title.display = true;
//                     chart.data.labels = labels;
//                     datasets.forEach(dataset => {
//                         chart.data.datasets.push(dataset);
//                     });
//                     chart.update();
//                 },
//                 error: () => console.log("Failed to fetch chart data from " + endpoint + "!")
//             });
//         }
//     }
// })

