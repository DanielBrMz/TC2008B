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
}
