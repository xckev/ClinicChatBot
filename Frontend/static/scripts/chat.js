var collap = document.getElementsByClassName("collapsible");
var open = false;

for (let i = 0; i < collap.length; i++) {
  collap[i].addEventListener("click", function () {
    this.classList.toggle("active");
    if(this.classList.contains("active")){
      document.getElementById("chat-button").innerHTML = 'Collapse Clinic Chatbot <i style="color: #fff;" class="fa fa-fw fa-comments-o"></i>';
    }
    else{
      document.getElementById("chat-button").innerHTML = 'Expand Clinic Chatbot <i style="color: #fff;" class="fa fa-fw fa-comments-o"></i>';
    }

    var content = this.nextElementSibling;

    if (content.style.maxHeight) {
      content.style.maxHeight = null;
    } else {
      content.style.maxHeight = content.scrollHeight + "px";
    }

  });
}

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}

function firstBotMessage() {
  let firstMessage = "Hello! Ask me any question about the clinic!"
  document.getElementById("botStarterMessage").innerHTML = '<p class="botText"><span>' + firstMessage + '</span></p>';

  document.getElementById("userInput").scrollIntoView(false);
}
firstBotMessage();

async function getResponse() {
  let userText = $("#textInput").val();

  if (userText == "") {
    alert("Ensure you input a value!");
  }

  let userHtml = '<p class="userText"><span>' + userText + '</span></p>';

  $("#textInput").val("");
  $("#chatbox").append(userHtml);
  document.getElementById("chat-bar-bottom").scrollIntoView(true);
    let botResponse = await getBotResponse(userText);
    let botHtml = '<p class="botText"><span>' + botResponse + '</span></p>';
    $("#chatbox").append(botHtml);

    document.getElementById("chat-bar-bottom").scrollIntoView(true);
}

async function getBotResponse(input) {
  if (input.toLowerCase() == "hello" || input.toLowerCase() == "hi") {
    await delay(1000);
    return "Hello there! I'm able to answer your questions about the clinic.";
  }
  else if (input.toLowerCase() == "goodbye" || input.toLowerCase() == "bye") {
    await delay(1000);
    return "Talk to you later!";
  }
  else {
    try {
      const resp = await await fetch("http://127.0.0.1:5000/response/" + input);
      // Check if the request was successful
      if (!resp.ok) {
        throw new Error(`HTTP error! status: ${resp.status}`);
      }
      console.log(resp);
      const data = await resp.json();
      console.log(data);
      console.log(data.response);
      return String(data.response); // This will be the resolved value of the promise returned by the async function
    } catch (error) {
      console.error("Failed to fetch data: ", error);
      // Handle errors or failed fetch attempts here
      return "Response failed."; // Or you could throw an error, depending on how you want to handle failures
    }
    
  }
}

function sendButton() {
  getResponse();
}

$("#textInput").keypress(function (e) {
  if (e.which == 13) {
    getResponse();
  }
});