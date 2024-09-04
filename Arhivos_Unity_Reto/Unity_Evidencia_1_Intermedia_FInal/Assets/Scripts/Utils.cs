using System.Collections.Generic;
using System.Data.Common;
using System.Threading.Tasks;
using System.Web;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class PositionData
{
    public int id;
    public Dictionary<char, int> position;
    // public bool is_holding;
}

[System.Serializable]
public class ActionSintax
{
    public int id;
    public string action;
    public string direction;
}



public class Utils : MonoBehaviour
{
    public static void SetLayerRecursivelyByName(GameObject obj, string layerName)
    {
        int newLayer = LayerMask.NameToLayer(layerName);
        if (newLayer == -1)
        {
            Debug.LogError($"Layer '{layerName}' does not exist.");
            return;
        }

        obj.layer = newLayer;

        foreach (Transform child in obj.transform)
        {
            SetLayerRecursivelyByName(child.gameObject, layerName);
        }
    }

    public static readonly Vector2Int[] directions = new Vector2Int[]
    {
        Vector2Int.up,
        Vector2Int.down,
        Vector2Int.left,
        Vector2Int.right
    };

    public static char Direction2Name(Vector2Int direction)
    {
        if (direction == Vector2Int.up) return 'F';
        if (direction == Vector2Int.down) return 'B';
        if (direction == Vector2Int.left) return 'L';
        if (direction == Vector2Int.right) return 'R';
        return 'E'; // Default case, should not happen with your current directions array
    }

    public static char OppositeDir(char direction)
    {
        switch (direction)
        {
            case 'F': return 'B';
            case 'B': return 'F';
            case 'L': return 'R';
            case 'R': return 'L';
            default: return direction;
        }
    }

    public static int DetermineColliderType(int layer)
    {
        if (layer == LayerMask.NameToLayer("Objects"))
            return 1; // Objects
        else if (layer == LayerMask.NameToLayer("Obstacles"))
            return 2; // Obstacles
        else if (layer == LayerMask.NameToLayer("Stacks"))
            return 3; // Stacks
        else
            return 0; // No collision or unknown layer
    }

    public static string Col2Type(int col)
    {
        switch (col)
        {
            case 1:
                return "Object";
            case 2:
                return "Obstacle";
            case 3:
                return "Stack";
            default:
                return "Undefined";
        }
    }

    public static async Task<string> SendGetRequestWithStructDataAsync(string baseUrl, string rawInfo)
    {

        using (UnityWebRequest webRequest = UnityWebRequest.Post(baseUrl, rawInfo, "application/json"))
        {
            var operation = webRequest.SendWebRequest();

            while (!operation.isDone)
            {
                await Task.Yield(); // Wait asynchronously until the request is done
            }

            if (webRequest.result == UnityWebRequest.Result.ConnectionError ||
                webRequest.result == UnityWebRequest.Result.DataProcessingError ||
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError($"Error: {webRequest.error}");
                return null;
            }
            else
            {
                return webRequest.downloadHandler.text;
            }
        }
    }

}
