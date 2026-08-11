const games = [
    "6s",
    "9s",
    "15s",
    "1min",
    "30s"
];


async function loadData(){

    let liveHTML = "";

    let statHTML = "";

    let trendHTML = "";


    for(let game of games){


        let res = await fetch(
            "/api/game/" + game
        );


        let d = await res.json();


        let latest = d.latest || {};

        let predict = d.predict || {};

        let stat = d.stat || {};



        let resultHTML = "";



        if(predict.result){


            if(
                predict.result.includes("命中")
            ){

                resultHTML = `

                <div class="win">
                √ 中
                </div>

                `;

            }
            else{


                resultHTML = `

                <div class="lose">
                × 挂
                </div>

                `;

            }


        }




        let numberClass =
            latest.result === "单"
            ?
            "single"
            :
            "double";





        liveHTML += `


        <div class="box">


            <h3>
            ${game}
            </h3>


            <div class="block">

            区块

            <br>

            ${latest.block || "-"}

            </div>



            <div class="number">

            ${latest.tail || "-"}

            </div>



            <div class="${numberClass}">

            ${latest.result || "-"}

            ${latest.size || ""}

            </div>



            <div class="predict">

            下一开奖:

            <br>

            ${predict.open_block || "-"}


            <br>


            预测:

            <b>
            ${predict.predict || "-"}
            </b>


            </div>


            ${resultHTML}


        </div>


        `;






        statHTML += `


        <div class="box">


            <h3>
            ${game}
            </h3>


            <div class="stat">


            最大连单:

            ${stat.single_max || 0}


            <br>


            最大连双:

            ${stat.double_max || 0}


            <br>


            当前:

            ${stat.current || "-"}


            </div>


        </div>


        `;







        let dots = "";


        if(stat.trend){


            stat.trend.forEach(item => {


                dots += `


                <span class="dot ${
                
                item === "单"
                ?
                "red"
                :
                "green"

                }">

                ${item}

                </span>


                `;


            });


        }




        trendHTML += `


        <div class="trend-box">


        <b>
        ${game}
        </b>


        <br>


        ${dots}


        </div>


        `;


    }




    document.getElementById(
        "live"
    ).innerHTML = liveHTML;



    document.getElementById(
        "stats"
    ).innerHTML = statHTML;



    document.getElementById(
        "trend"
    ).innerHTML = trendHTML;



    loadHistory();


}




async function loadHistory(){


    let html = "";


    for(let game of games){


        html += `


        <div class="history-box">


        <h3>
        ${game} 历史
        </h3>


        暂无历史统计


        </div>


        `;


    }



    document.getElementById(
        "history"
    ).innerHTML = html;


}





loadData();


setInterval(
    loadData,
    5000
);