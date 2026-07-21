async function generate(){


let username =
document.getElementById(
"username"
).value;



if(!username){

alert(
"Enter username"
);

return;

}



let response =
await fetch(
"https://YOUR-BACKEND-URL/generate",
{

method:"POST",

headers:{

"Content-Type":
"application/json"

},


body:
JSON.stringify(
{
username:username
}
)

}

);



let blob =
await response.blob();



let url =
URL.createObjectURL(
blob
);



document.getElementById(
"result"
).src=url;



document.getElementById(
"download"
).href=url;



document.getElementById(
"download"
).download=
"UNDESIRABLE_"+username+".png";


}
