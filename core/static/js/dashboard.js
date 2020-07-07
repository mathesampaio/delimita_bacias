/* globals Chart:false, feather:false */

(function () {
  'use strict'

  feather.replace()

  // Graphs
  var ctx = document.getElementById('myChart')
  // eslint-disable-next-line no-unused-vars

var diaInicial = new Date('01-01-2019');
var diaFinal = new Date('2012-01-01');
var novaData = diaInicial;
var tabela=[];
var dados =[];
if (novaData > diaFinal) {
    novaData = diaFinal;
    diaFinal = diaInicial;
}
var ale = 10;
while (novaData < diaFinal) {
    novaData = new Date(novaData.getTime() + (24 * 60 * 60 * 1000));
    var dataFormatada = novaData.getFullYear() + '-' + (novaData.getMonth() + 1) + '-' + novaData.getDate();
    tabela.push(dataFormatada);
    dados = (ale + 1);
}



  var myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels:[tabela],
      datasets: [{
        data: [dados],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      scales: {
        yAxes: [{
          ticks: {
            beginAtZero: true
          }
        }]
      },
      legend: {
        display: false
      }
    }
  })
}())