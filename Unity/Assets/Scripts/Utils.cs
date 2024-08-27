using System.Collections;
using System.Collections.Generic;
using System.Net.NetworkInformation;
using UnityEngine;

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
}
