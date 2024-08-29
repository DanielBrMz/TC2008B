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
            parentAgent.hasCollided = true;
        }
        else
        {
            ;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        BoxCollider boxCollider = other.GetComponent<BoxCollider>();
        if (boxCollider != null)
        {
            parentAgent.hasCollided = false;        }
        else
        {
            ;
        }
    }
}
