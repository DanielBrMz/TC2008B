using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Threading;
using System.Threading.Tasks;

public class Stack : MonoBehaviour
{
    [Header("Stack values")]
    public int id;
    public Vector2Int pos;
    public int nItems = 0;
    public List<Object> items;
    public int maxItems = 5;  // Set this to your desired maximum stack size 

    [Header("Engine values")]
    public Enviroment parentEnv;
    

    private float verticalItemOffset = 0.2f; // Adjust this value as needed
    private float itemScale = 0.8f; // Adjust this value as needed
    private bool isLocked = false;

    private void Awake()
    {
        transform.localScale = new Vector3(Enviroment.tileSize - 0.5f, Enviroment.tileSize/3*2, Enviroment.tileSize - 0.5f);
        transform.position += new Vector3(0f,Enviroment.tileSize/3,0f);
        items = new List<Object>();
    }

    public Vector3 GetNextItemPosition()
    {
        return transform.position + Vector3.up * (nItems * verticalItemOffset);
    }

    public bool TryLockForDropAsync()
    {
        if (isLocked || nItems >= maxItems)
            return false;

        isLocked = true;
        return true;
    }

    public void UnlockForDrop()
    {
        isLocked = false;
    }


    public bool TryAddItemAsync(Object item)
    {
        if (nItems >= maxItems)
            return false;

        items.Add(item);
        nItems++;

        // Scale down the item
        item.transform.localScale *= itemScale;

        // Position the item
        item.transform.position = GetNextItemPosition();

        // Disable item's collider
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null)
            itemCollider.enabled = false;

        // Check if stack is full after adding item
        if (nItems >= maxItems)
        {
            gameObject.layer = LayerMask.NameToLayer("Obstacle");
        }

        return true;
    }
}