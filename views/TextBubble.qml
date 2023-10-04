import QtQuick 2.15

Rectangle {
    id: bubble
    property string text: ""
    property string sender: "user"

    width: textBubble.width + 20
    height: textBubble.height + 20

    color: sender === "user" ? "#3684ac" : "#676767"
    radius: 10

    Text {
        id: textBubble
        text: bubble.text
        color: "white"
        wrapMode: Text.Wrap
        width: 30 // set the desired width here
        padding: 10
        anchors.centerIn: parent
    }

    Text {
        id: textBubble
        text: bubble.text
        color: "white"
        wrapMode: Text.WrapAnywhere
        padding: 10
        anchors.centerIn: parent
    }
}