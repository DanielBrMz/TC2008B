using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ContactTrigger : MonoBehaviour
{
    public Agent parentAgent;

    private void OnTriggerEnter(Collider other)
    {
        BoxCollider boxCollider = other.GetComponent<BoxCollider>();
        if (boxCollider != null)
        {
            int value = Utils.DetermineColliderType(other.gameObject.layer);
            // Debug.LogError($"Ag:{parentAgent.id} collided with an {Utils.Col2Type(value)}!");

            // The collider is a BoxCollider, proceed with your logic
            parentAgent.hasCollided = true;
            // Your logic here
        }
        else
        {
            ;// The collider is not a BoxCollider, you can choose to ignore it or handle differently
        }
    }

    private void OnTriggerExit(Collider other)
    {
        BoxCollider boxCollider = other.GetComponent<BoxCollider>();
        if (boxCollider != null)
        {
            parentAgent.hasCollided = false;
            // Your logic here
        }
        else
        {
            ;
        }
    }
}
